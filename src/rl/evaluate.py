"""Evaluate a trained agent: N games vs each bot, win rate with 95% Wilson CI.

    python -m src.rl.evaluate --model models/<run_id> --games 1000
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .agent import RLAgent
from .stats import wilson_ci


def evaluate(agent: RLAgent, opponent: str, games: int, seed: int = 10_000, env_kwargs: dict | None = None) -> dict:
    kwargs = dict(env_kwargs or {})
    kwargs["opponent"] = opponent
    env = agent.make_env(**kwargs)
    wins = losses = draws = rounds = bankrupt = invalid = steps = 0
    for g in range(games):
        obs, _ = env.reset(seed=seed + g)
        while True:
            obs, _, terminated, _, info = env.step(agent.predict(obs, env.action_masks()))
            steps += 1
            if terminated:
                break
        winner = info["winner"]
        wins += winner == 0
        losses += winner == 1
        draws += winner is None
        rounds += info["rounds"]
        bankrupt += info["end_reason"] == "bankruptcy"
        invalid += info["invalid_actions"]
    lo, hi = wilson_ci(wins, games)
    return {
        "opponent": opponent,
        "games": games,
        "wins": wins,
        "losses": losses,
        "draws": draws,
        "win_rate": wins / games,
        "ci_low": lo,
        "ci_high": hi,
        "mean_rounds": rounds / games,
        "bankruptcy_rate": bankrupt / games,
        "invalid_action_rate": invalid / max(steps, 1),
    }


def evaluate_bot_vs_bot(bot_a: str, bot_b: str, games: int, seed: int = 10_000) -> dict:
    """Baseline row for the results table (seat 0 = bot_a)."""
    from src.bots import make_bot
    from src.engine import Game

    wins = 0
    for g in range(games):
        game = Game(seed=seed + g)
        wins += game.play([make_bot(bot_a, seed + g), make_bot(bot_b, seed + g + 1)]) == 0
    lo, hi = wilson_ci(wins, games)
    return {"agent": bot_a, "opponent": bot_b, "games": games, "wins": wins,
            "win_rate": wins / games, "ci_low": lo, "ci_high": hi}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, help="path to models/<run_id> (with or without .zip)")
    parser.add_argument("--games", type=int, default=1000)
    parser.add_argument("--opponents", nargs="+", default=["random", "fixed", "greedy"])
    parser.add_argument("--out", default="results/eval")
    args = parser.parse_args()

    agent = RLAgent.load(args.model)
    env_kwargs = {k: agent.meta["config"][k] for k in ("reward", "use_masking")}
    rows = [evaluate(agent, opp, args.games, env_kwargs=env_kwargs) for opp in args.opponents]
    run_id = Path(args.model).with_suffix("").name
    out = Path(args.out) / f"{run_id}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"run_id": run_id, "meta": agent.meta, "results": rows}, indent=2))
    for r in rows:
        print(f"{run_id} vs {r['opponent']:>6}: {r['win_rate']:.1%} "
              f"[{r['ci_low']:.1%}, {r['ci_high']:.1%}]  rounds={r['mean_rounds']:.0f}")


if __name__ == "__main__":
    main()
