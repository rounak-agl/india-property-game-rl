"""Registry of trained models found in models/*.json."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from src.rl.agent import RLAgent

MODELS_DIR = Path("models")
EVAL_DIR = Path("results/eval")


def list_agents() -> list[dict]:
    agents = []
    for meta_path in sorted(MODELS_DIR.glob("*.json")):
        if not meta_path.with_suffix(".zip").exists():
            continue
        meta = json.loads(meta_path.read_text())
        win_rates = {}
        eval_path = EVAL_DIR / meta_path.name
        if eval_path.exists():
            win_rates = {r["opponent"]: r["win_rate"] for r in json.loads(eval_path.read_text())["results"]}
        agents.append({
            "id": meta["run_id"],
            "algo": meta["algo"],
            "env": meta["env"],
            "trained_vs": meta["config"]["opponent"],
            "reward": meta["config"]["reward"]["mode"],
            "steps": meta["steps"],
            "win_rates": win_rates,
        })
    if agents:
        best = max(agents, key=lambda a: a["win_rates"].get("fixed", -1.0))
        for a in agents:
            a["default"] = a is best
    return agents


@lru_cache(maxsize=16)
def load_agent(agent_id: str) -> RLAgent:
    path = MODELS_DIR / agent_id
    if path.resolve().parent != MODELS_DIR.resolve() or not path.with_suffix(".zip").exists():
        raise KeyError(agent_id)
    return RLAgent.load(path)


def default_agent_id() -> str | None:
    return next((a["id"] for a in list_agents() if a.get("default")), None)
