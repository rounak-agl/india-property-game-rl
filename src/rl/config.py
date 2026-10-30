"""Experiment configuration (one YAML file per experiment in experiments/)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path

import yaml

ALGOS = ("dqn", "ppo", "maskppo")


@dataclass
class TrainConfig:
    name: str
    algo: str = "maskppo"
    env: str = "B"
    opponent: str = "fixed"
    use_masking: bool = True
    reward: dict = field(default_factory=lambda: {"mode": "delta_share", "terminal": 10.0})
    steps: int = 300_000
    seeds: list[int] = field(default_factory=lambda: [0, 1, 2])
    n_envs: int = 8
    net_arch: list[int] = field(default_factory=lambda: [128, 128])
    algo_kwargs: dict = field(default_factory=dict)
    eval_every: int = 20_000
    eval_games: int = 100
    eval_opponents: list[str] = field(default_factory=lambda: ["fixed", "random"])
    final_games: int = 1000

    def __post_init__(self):
        if self.algo not in ALGOS:
            raise ValueError(f"algo must be one of {ALGOS}")
        if self.algo == "maskppo" and self.env.upper() != "B":
            raise ValueError("maskppo needs env B (action masks)")

    @classmethod
    def load(cls, path: str | Path) -> TrainConfig:
        return cls(**yaml.safe_load(Path(path).read_text()))

    def env_kwargs(self, opponent: str | None = None) -> dict:
        return {"opponent": opponent or self.opponent, "reward": dict(self.reward), "use_masking": self.use_masking}

    def run_id(self, seed: int) -> str:
        return f"{self.name}_s{seed}"

    def to_dict(self) -> dict:
        return asdict(self)
