"""Aggregate experiment outputs into results/summary/summary.json and results/figures/*.png.

    python -m src.rl.make_plots [--behaviour-games 300]

Every number shown in the UI, README or slides should come from summary.json.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from src.engine.board_data import GROUP_NAMES, TILES  # noqa: E402

from .agent import RLAgent  # noqa: E402
from .evaluate import evaluate_bot_vs_bot  # noqa: E402
from .stats import wilson_ci  # noqa: E402

EVAL_DIR = Path("results/eval")
RAW_DIR = Path("results/raw")
SUMMARY = Path("results/summary/summary.json")
FIG_DIR = Path("results/figures")

LABELS = {
    "e1_dqn_a": "DQN · Env A",
    "e1_ppo_a": "PPO · Env A",
    "e2_dqn_b_unmasked": "DQN · Env B (no mask)",
    "e2_ppo_b_unmasked": "PPO · Env B (no mask)",
    "e2_maskppo_b": "MaskablePPO · Env B",
    "e3_maskppo_b_absolute": "MaskablePPO · absolute reward",
    "e3_maskppo_b_sparse": "MaskablePPO · sparse reward",
    "e4_maskppo_b_nobonus": "MaskablePPO · no property bonus",
    "e5_maskppo_b_mixed": "MaskablePPO · trained vs mixed",
    "e6_maskppo_b_long": "MaskablePPO · 1M steps, larger net",
}
EXPERIMENTS = {
    "E1 Algorithm (blueprint env)": ["e1_dqn_a", "e1_ppo_a"],
    "E2 Env design & masking": ["e1_ppo_a", "e2_ppo_b_unmasked", "e2_dqn_b_unmasked", "e2_maskppo_b"],
    "E3 Reward design": ["e2_maskppo_b", "e3_maskppo_b_absolute", "e3_maskppo_b_sparse"],
    "E4 Property bonus": ["e2_maskppo_b", "e4_maskppo_b_nobonus"],
    "E5 Training opponent": ["e2_maskppo_b", "e5_maskppo_b_mixed"],
    "E6 Longer training": ["e2_maskppo_b", "e6_maskppo_b_long"],
}
OPPONENTS = ("random", "fixed", "greedy")


def config_name(run_id: str) -> str:
    return run_id.rsplit("_s", 1)[0]


def aggregate_final() -> dict[str, dict]:
    runs: dict[str, list[dict]] = defaultdict(list)
    for path in sorted(EVAL_DIR.glob("*.json")):
        runs[config_name(path.stem)].append(json.loads(path.read_text()))
    out = {}
    for name, seeds in runs.items():
        row = {"label": LABELS.get(name, name), "seeds": len(seeds), "run_ids": [s["run_id"] for s in seeds],
               "algo": seeds[0]["meta"]["algo"], "env": seeds[0]["meta"]["env"],
               "train_minutes": round(np.mean([s["meta"]["train_seconds"] for s in seeds]) / 60, 1), "vs": {}}
        for opp in OPPONENTS:
            rs = [r for s in seeds for r in s["results"] if r["opponent"] == opp]
            wins, games = sum(r["wins"] for r in rs), sum(r["games"] for r in rs)
            lo, hi = wilson_ci(wins, games)
            rates = [r["win_rate"] for r in rs]
            row["vs"][opp] = {
                "win_rate": wins / games, "ci_low": lo, "ci_high": hi, "games": games,
                "seed_std": float(np.std(rates)), "per_seed": rates,
                "mean_rounds": float(np.mean([r["mean_rounds"] for r in rs])),
                "bankruptcy_rate": float(np.mean([r["bankruptcy_rate"] for r in rs])),
                "invalid_action_rate": float(np.mean([r["invalid_action_rate"] for r in rs])),
            }
        out[name] = row
    return out


def learning_curves() -> dict[str, dict]:
    frames = defaultdict(list)
    for csv in RAW_DIR.glob("*/eval.csv"):
        df = pd.read_csv(csv)
        df["run"] = csv.parent.name
        frames[config_name(csv.parent.name)].append(df)
    curves = {}
    for name, dfs in frames.items():
        df = pd.concat(dfs)
        df["bucket"] = (df["timesteps"] / 50_000).round().astype(int) * 50_000
        curves[name] = {}
        for opp, g in df.groupby("opponent"):
            agg = g.groupby("bucket")["win_rate"].agg(["mean", "std"]).fillna(0).reset_index()
            curves[name][opp] = {"timesteps": agg["bucket"].tolist(), "mean": agg["mean"].round(4).tolist(),
                                 "std": agg["std"].round(4).tolist()}
    return curves


def behaviour(best: str, games: int) -> dict:
    """How the best agent plays: buy rate per group when it is offered a purchase."""
    agent = RLAgent.load(Path("models") / best)
    env = agent.make_env(opponent="fixed", **{k: agent.meta["config"][k] for k in ("reward", "use_masking")})
    offered, bought = defaultdict(int), defaultdict(int)
    cash_at_buy, cash_at_pass = [], []
    for g in range(games):
        obs, _ = env.reset(seed=90_000 + g)
        while True:
            d = env.decision
            action = agent.predict(obs, env.action_masks())
            if d is not None and d.kind in ("buy", "turn") and TILES[d.tile].buyable \
                    and env.game.state.tiles[d.tile].owner is None:
                group = GROUP_NAMES[TILES[d.tile].group]
                cash = env.game.state.players[0].cash
                offered[group] += 1
                if action == 1:
                    bought[group] += 1
                    cash_at_buy.append(cash)
                else:
                    cash_at_pass.append(cash)
            obs, _, done, _, _ = env.step(action)
            if done:
                break
    return {
        "model": best, "games": games,
        "buy_rate_by_group": {g: bought[g] / offered[g] for g in GROUP_NAMES.values() if offered[g]},
        "offers_by_group": dict(offered),
        "mean_cash_when_buying": float(np.mean(cash_at_buy)) if cash_at_buy else None,
        "mean_cash_when_passing": float(np.mean(cash_at_pass)) if cash_at_pass else None,
    }


def plot(final: dict, curves: dict, baselines: list[dict]) -> list[str]:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    files = []
    plt.rcParams.update({"figure.dpi": 140, "font.size": 10, "axes.spines.top": False, "axes.spines.right": False})

    fig, ax = plt.subplots(figsize=(8, 4.5))
    for name, c in sorted(curves.items()):
        if "fixed" in c:
            t, m, s = (np.array(c["fixed"][k]) for k in ("timesteps", "mean", "std"))
            ax.plot(t, m, label=LABELS.get(name, name))
            ax.fill_between(t, m - s, m + s, alpha=0.15)
    ax.axhline(0.5, ls="--", c="grey", lw=1)
    ax.set(xlabel="training timesteps", ylabel="win rate vs Fixed-Policy bot", ylim=(0, 1),
           title="Learning curves (mean ± std over seeds)")
    ax.legend(fontsize=7, loc="lower right")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "learning_curves.png")
    files.append("learning_curves.png")
    plt.close(fig)

    names = [n for n in LABELS if n in final]
    fig, ax = plt.subplots(figsize=(9, 4.8))
    width, x = 0.27, np.arange(len(names))
    for k, opp in enumerate(OPPONENTS):
        rates = np.array([final[n]["vs"][opp]["win_rate"] for n in names])
        err = np.array([[final[n]["vs"][opp]["win_rate"] - final[n]["vs"][opp]["ci_low"],
                         final[n]["vs"][opp]["ci_high"] - final[n]["vs"][opp]["win_rate"]] for n in names]).T
        ax.bar(x + (k - 1) * width, rates, width, yerr=np.clip(err, 0, None), capsize=2, label=f"vs {opp}")
    for b in baselines:
        if b["agent"] == "fixed" and b["opponent"] == "random":
            ax.axhline(b["win_rate"], ls=":", c="black", lw=1, label="Fixed bot vs Random (baseline)")
    ax.axhline(0.5, ls="--", c="grey", lw=1)
    ax.set_xticks(x, [LABELS[n] for n in names], rotation=30, ha="right", fontsize=8)
    ax.set(ylabel="win rate (1,000 games/seed, 95% CI)", ylim=(0, 1), title="Final evaluation")
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "final_comparison.png")
    files.append("final_comparison.png")
    plt.close(fig)
    return files


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--behaviour-games", type=int, default=300)
    parser.add_argument("--baseline-games", type=int, default=1000)
    args = parser.parse_args()

    final = aggregate_final()
    if not final:
        raise SystemExit("no results in results/eval/; train something first")
    curves = learning_curves()
    baselines = [evaluate_bot_vs_bot(a, b, args.baseline_games)
                 for a, b in (("fixed", "random"), ("greedy", "random"), ("greedy", "fixed"), ("random", "random"))]
    best_cfg = max(final, key=lambda n: final[n]["vs"]["fixed"]["win_rate"])
    best_run = max(final[best_cfg]["run_ids"],
                   key=lambda r: json.loads((EVAL_DIR / f"{r}.json").read_text())["results"][1]["win_rate"])
    summary = {
        "final": final,
        "curves": curves,
        "experiments": {k: [n for n in v if n in final] for k, v in EXPERIMENTS.items()},
        "baselines": baselines,
        "best": {"config": best_cfg, "run_id": best_run},
        "behaviour": behaviour(best_run, args.behaviour_games),
    }
    summary["figures"] = plot(final, curves, baselines)
    SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY.write_text(json.dumps(summary, indent=2))
    print(f"{'config':<28} {'random':>8} {'fixed':>8} {'greedy':>8}")
    for n, r in final.items():
        print(f"{n:<28} " + " ".join(f"{r['vs'][o]['win_rate']:>8.1%}" for o in OPPONENTS))
    print(f"best: {best_run}; wrote {SUMMARY} and {FIG_DIR}/")


if __name__ == "__main__":
    main()
