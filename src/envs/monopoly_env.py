"""Gymnasium environments.

The agent always sits in seat 0; who moves first is random every episode (D-010).
The opponent bot and the agent's jail decisions (D-011) are played inside step().
"""

from __future__ import annotations

from typing import Any

import gymnasium as gym
import numpy as np

from src.bots import jail_policy, make_bot
from src.engine import Decision, Game
from src.engine.state import N_ACTIONS, PASS

from .observation import OBS_A_SIZE, OBS_B_SIZE, encode_a, encode_b
from .rewards import RewardConfig, net_worth_share, step_reward, terminal_reward

AGENT = 0
OPPONENTS = ("random", "fixed", "greedy", "mixed")


class MonopolyEnv(gym.Env):
    metadata = {"render_modes": []}
    blueprint = False

    def __init__(
        self,
        opponent: str = "fixed",
        reward: RewardConfig | dict | None = None,
        max_rounds: int = 200,
        use_masking: bool = True,
    ):
        if opponent not in OPPONENTS:
            raise ValueError(f"unknown opponent {opponent!r}; choose from {OPPONENTS}")
        self.opponent_name = opponent
        self.reward_cfg = reward if isinstance(reward, RewardConfig) else RewardConfig(**(reward or {}))
        self.max_rounds = max_rounds
        self.use_masking = use_masking
        self.game: Game | None = None
        self.decision: Decision | None = None
        self.opponent = None
        self.prev_share = 0.5
        self.invalid_actions = 0

    # ------------------------------------------------------------------ gym API
    def reset(self, *, seed: int | None = None, options: dict | None = None):
        super().reset(seed=seed)
        while True:
            game_seed = int(self.np_random.integers(2**31))
            opp = self.opponent_name
            if opp == "mixed":
                opp = ("random", "fixed", "greedy")[int(self.np_random.integers(3))]
            self.opponent = make_bot(opp, game_seed + 1)
            self.game = Game(
                seed=game_seed,
                names=("RL Agent", f"{opp.title()} Bot"),
                max_rounds=self.max_rounds,
                blueprint_players={AGENT} if self.blueprint else (),
            )
            self.invalid_actions = 0
            self.decision = self._run_to_agent_decision()
            if self.decision is not None:
                break
        self.prev_share = self._share()
        return self._obs(), self._info()

    def step(self, action: int):
        assert self.game is not None and self.decision is not None, "call reset() first"
        action = int(action)
        if action not in self.decision.legal:
            self.invalid_actions += 1
            action = PASS  # invalid choices act as Pass (unmasked ablation)
        n_events = len(self.game.events)
        self.game.act(action)
        if self.blueprint and action != PASS:
            # Env A lists every action as legal; Buy/Build that had no effect count as invalid.
            effect = {"bought", "built"}
            if not any(e.type in effect and e.player == AGENT for e in self.game.events[n_events:]):
                self.invalid_actions += 1
        self.decision = self._run_to_agent_decision()

        share = self._share()
        reward = step_reward(self.prev_share, share, self.reward_cfg)
        self.prev_share = share
        terminated = self.game.finished
        if terminated:
            reward += terminal_reward(self.game.state.winner, AGENT, self.reward_cfg)
        return self._obs(), float(reward), terminated, False, self._info()

    # ------------------------------------------------------------------ helpers
    def _run_to_agent_decision(self) -> Decision | None:
        game = self.game
        decision = game.advance()
        while decision is not None:
            if decision.player != AGENT:
                decision = game.act(self.opponent.decide(game, decision))
            elif decision.kind == "jail":
                decision = game.act(jail_policy(game, decision))
            else:
                return decision
        return None

    def _share(self) -> float:
        return net_worth_share(self.game.state, AGENT, self.reward_cfg)

    def _info(self) -> dict[str, Any]:
        s = self.game.state
        return {
            "winner": s.winner,
            "finished": s.finished,
            "rounds": s.round,
            "end_reason": s.end_reason,
            "share": self.prev_share,
            "invalid_actions": self.invalid_actions,
            "decision": self.decision.kind if self.decision else None,
        }

    def _obs(self) -> np.ndarray:
        raise NotImplementedError

    def action_masks(self) -> np.ndarray:
        mask = np.zeros(self.action_space.n, dtype=bool)
        if self.decision is None:
            mask[PASS] = True
        elif not self.use_masking:
            mask[:] = True
        else:
            mask[self.decision.legal] = True
        return mask


class EnvA(MonopolyEnv):
    """Blueprint env: 32-dim obs, Discrete(3) asked after every agent move, invalid -> Pass."""

    blueprint = True

    def __init__(self, **kwargs):
        kwargs.setdefault("use_masking", False)
        super().__init__(**kwargs)
        self.observation_space = gym.spaces.Box(-1.0, 5.0, (OBS_A_SIZE,), np.float32)
        self.action_space = gym.spaces.Discrete(3)

    def _obs(self) -> np.ndarray:
        return encode_a(self.game.state, AGENT)


class EnvB(MonopolyEnv):
    """Masked env: 133-dim obs, Discrete(10) only at real decision points, action_masks()."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.observation_space = gym.spaces.Box(0.0, 1.0, (OBS_B_SIZE,), np.float32)
        self.action_space = gym.spaces.Discrete(N_ACTIONS)

    def _obs(self) -> np.ndarray:
        return encode_b(self.game.state, AGENT, self.decision, self.prev_share)


def make_env(env: str = "B", **kwargs) -> MonopolyEnv:
    return {"A": EnvA, "B": EnvB}[env.upper()](**kwargs)
