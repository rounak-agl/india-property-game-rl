"""Train one experiment config for each of its seeds.

    python -m src.rl.train --config experiments/e2_maskppo_b.yaml [--seeds 0 1] [--steps 50000]

Writes models/<run_id>.zip + .json, results/raw/<run_id>/{eval.csv,monitor.csv}
and the final 1,000-game evaluation to results/eval/<run_id>.json.
"""

from __future__ import annotations

import argparse
import csv
import json
import time
from datetime import UTC, datetime
from pathlib import Path

import torch
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.monitor import Monitor

from src.envs import make_env

from .agent import ALGO_CLASSES, RLAgent
from .config import TrainConfig
from .evaluate import evaluate

MODELS_DIR = Path("models")
RAW_DIR = Path("results/raw")
EVAL_DIR = Path("results/eval")

DEFAULT_ALGO_KWARGS = {
    "dqn": {
        "learning_rate": 1e-4,
        "buffer_size": 100_000,
        "learning_starts": 5_000,
        "batch_size": 128,
        "gamma": 0.99,
        "train_freq": 4,
        "target_update_interval": 2_000,
        "exploration_fraction": 0.3,
        "exploration_final_eps": 0.05,
    },
    "ppo": {"learning_rate": 3e-4, "n_steps": 1024, "batch_size": 256, "gamma": 0.99, "ent_coef": 0.01},
    "maskppo": {"learning_rate": 3e-4, "n_steps": 1024, "batch_size": 256, "gamma": 0.99, "ent_coef": 0.01},
}


class PeriodicEval(BaseCallback):
    """Every `every` timesteps, play `games` games vs each opponent and append to a CSV."""

    def __init__(self, cfg: TrainConfig, csv_path: Path):
        super().__init__()
        self.cfg, self.csv_path, self.next_eval = cfg, csv_path, 0

    def _on_step(self) -> bool:
        if self.num_timesteps >= self.next_eval:
            self.next_eval += self.cfg.eval_every
            self._run_eval()
        return True

    def _on_training_end(self) -> None:
        self._run_eval()

    def _run_eval(self) -> None:
        agent = RLAgent(self.model, self.cfg.algo, self.cfg.env)
        new_file = not self.csv_path.exists()
        with self.csv_path.open("a", newline="") as f:
            writer = csv.writer(f)
            if new_file:
                writer.writerow(["timesteps", "opponent", "games", "win_rate", "ci_low", "ci_high", "mean_rounds"])
            for opp in self.cfg.eval_opponents:
                r = evaluate(agent, opp, self.cfg.eval_games, seed=50_000, env_kwargs=self.cfg.env_kwargs(opp))
                writer.writerow([self.num_timesteps, opp, r["games"], f"{r['win_rate']:.4f}",
                                 f"{r['ci_low']:.4f}", f"{r['ci_high']:.4f}", f"{r['mean_rounds']:.1f}"])
                if self.verbose:
                    print(f"  [{self.num_timesteps:>7}] vs {opp}: {r['win_rate']:.1%}")


def train_one(cfg: TrainConfig, seed: int, verbose: int = 1) -> dict:
    run_id = cfg.run_id(seed)
    raw = RAW_DIR / run_id
    raw.mkdir(parents=True, exist_ok=True)
    for stale in ("eval.csv", "monitor.csv"):
        (raw / stale).unlink(missing_ok=True)
    MODELS_DIR.mkdir(exist_ok=True)

    n_envs = 1 if cfg.algo == "dqn" else cfg.n_envs
    vec_env = make_vec_env(lambda: Monitor(make_env(cfg.env, **cfg.env_kwargs())), n_envs=n_envs, seed=seed)
    algo_kwargs = {**DEFAULT_ALGO_KWARGS[cfg.algo], **cfg.algo_kwargs}
    model = ALGO_CLASSES[cfg.algo](
        "MlpPolicy", vec_env, seed=seed, verbose=0, device="cpu",
        policy_kwargs={"net_arch": cfg.net_arch}, **algo_kwargs,
    )
    callback = PeriodicEval(cfg, raw / "eval.csv")
    callback.verbose = verbose
    start = time.time()
    model.learn(total_timesteps=cfg.steps, callback=callback)
    seconds = time.time() - start

    meta = {
        "run_id": run_id,
        "algo": cfg.algo,
        "env": cfg.env.upper(),
        "seed": seed,
        "steps": cfg.steps,
        "train_seconds": round(seconds, 1),
        "trained_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "config": cfg.to_dict(),
        "algo_kwargs": algo_kwargs,
    }
    model.save(MODELS_DIR / f"{run_id}.zip")
    (MODELS_DIR / f"{run_id}.json").write_text(json.dumps(meta, indent=2))

    agent = RLAgent(model, cfg.algo, cfg.env, meta)
    final = [evaluate(agent, opp, cfg.final_games, env_kwargs=cfg.env_kwargs(opp))
             for opp in ("random", "fixed", "greedy")]
    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    (EVAL_DIR / f"{run_id}.json").write_text(json.dumps({"run_id": run_id, "meta": meta, "results": final}, indent=2))
    if verbose:
        summary = ", ".join(f"{r['opponent']} {r['win_rate']:.1%}" for r in final)
        print(f"{run_id}: trained {cfg.steps} steps in {seconds / 60:.1f} min | final: {summary}")
    return meta


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--seeds", type=int, nargs="+")
    parser.add_argument("--steps", type=int)
    parser.add_argument("--threads", type=int, default=1, help="torch CPU threads (keep 1 to run configs in parallel)")
    args = parser.parse_args()

    torch.set_num_threads(args.threads)
    cfg = TrainConfig.load(args.config)
    if args.steps:
        cfg.steps = args.steps
    for seed in args.seeds if args.seeds is not None else cfg.seeds:
        train_one(cfg, seed)


if __name__ == "__main__":
    main()
