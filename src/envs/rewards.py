"""Reward functions (TECH_SPEC §4.4, decision D-008)."""

from __future__ import annotations

from dataclasses import dataclass

from src.engine.rules import weighted_net_worth
from src.engine.state import GameState

REWARD_MODES = ("delta_share", "absolute_share", "sparse")


@dataclass(frozen=True)
class RewardConfig:
    mode: str = "delta_share"
    terminal: float = 10.0  # c in Bonjour, Haliem et al. (2022) Eq. 1
    b_single: float = 1.5
    b_monopoly: float = 2.0

    def __post_init__(self):
        if self.mode not in REWARD_MODES:
            raise ValueError(f"unknown reward mode {self.mode!r}; choose from {REWARD_MODES}")


def net_worth_share(state: GameState, agent: int, cfg: RewardConfig) -> float:
    """share = nw_agent / (nw_agent + nw_opponent), using the weighted net worth."""
    mine = weighted_net_worth(state, agent, cfg.b_single, cfg.b_monopoly)
    theirs = weighted_net_worth(state, 1 - agent, cfg.b_single, cfg.b_monopoly)
    total = mine + theirs
    return 0.5 if total <= 0 else mine / total


def step_reward(prev_share: float, share: float, cfg: RewardConfig) -> float:
    if cfg.mode == "delta_share":
        return share - prev_share
    if cfg.mode == "absolute_share":
        return share
    return 0.0


def terminal_reward(winner: int | None, agent: int, cfg: RewardConfig) -> float:
    if winner is None:
        return 0.0
    return cfg.terminal if winner == agent else -cfg.terminal
