"""Load a trained model and query it, including the "X-Ray" explanation data."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch
from sb3_contrib import MaskablePPO
from stable_baselines3 import DQN, PPO

from src.envs import MonopolyEnv, make_env

ALGO_CLASSES = {"dqn": DQN, "ppo": PPO, "maskppo": MaskablePPO}
ACTION_NAMES = {
    "A": ["Pass", "Buy", "Build"],
    "B": ["Pass", "Buy"] + [f"Build:{g}" for g in
                            ("Brown", "Light Blue", "Pink", "Orange", "Red", "Yellow", "Green", "Dark Blue")],
}


@dataclass
class XRay:
    actions: list[str]
    legal: list[bool]
    probs: list[float] | None
    q_values: list[float] | None
    value: float | None
    chosen: int

    def to_dict(self) -> dict:
        return self.__dict__.copy()


class RLAgent:
    def __init__(self, model, algo: str, env: str, meta: dict | None = None):
        self.model, self.algo, self.env_name, self.meta = model, algo, env.upper(), meta or {}

    @classmethod
    def load(cls, path: str | Path) -> RLAgent:
        path = Path(path)
        meta = json.loads(path.with_suffix(".json").read_text())
        model = ALGO_CLASSES[meta["algo"]].load(path.with_suffix(".zip"), device="cpu")
        return cls(model, meta["algo"], meta["env"], meta)

    def make_env(self, **kwargs) -> MonopolyEnv:
        return make_env(self.env_name, **kwargs)

    def predict(self, obs: np.ndarray, mask: np.ndarray, deterministic: bool = True) -> int:
        if self.algo == "maskppo":
            action, _ = self.model.predict(obs, action_masks=mask, deterministic=deterministic)
        else:
            action, _ = self.model.predict(obs, deterministic=deterministic)
        return int(action)

    def xray(self, obs: np.ndarray, mask: np.ndarray) -> XRay:
        """Action probabilities (PPO family) or Q-values (DQN) for one observation."""
        policy = self.model.policy
        obs_t, _ = policy.obs_to_tensor(obs)
        probs = q_values = value = None
        with torch.no_grad():
            if self.algo == "dqn":
                q_values = policy.q_net(obs_t)[0].cpu().numpy().tolist()
                value = float(max(q for q, ok in zip(q_values, mask, strict=True) if ok))
            else:
                kwargs = {"action_masks": mask} if self.algo == "maskppo" else {}
                dist = policy.get_distribution(obs_t, **kwargs)
                probs = dist.distribution.probs[0].cpu().numpy().tolist()
                value = float(policy.predict_values(obs_t)[0].item())
        chosen = self.predict(obs, mask)
        return XRay(ACTION_NAMES[self.env_name], mask.tolist(), probs, q_values, value, chosen)
