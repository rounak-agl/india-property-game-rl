"""Baseline opponents.

- RandomBot: buys / builds with probability 0.5 (blueprint baseline).
- FixedPolicyBot: Bailis et al. (2014) thresholds; spends only when cash > 350.
  (Their "sell when cash < 150" rule is covered by the engine's forced liquidation.)
- GreedyBot: always buys and builds when legal.
Jail decisions use one shared rule for every player, including the RL agent (D-011).
"""

from __future__ import annotations

import random

from src.engine import Decision, Game
from src.engine.state import BUY, JAIL_CARD, JAIL_PAY, JAIL_ROLL, PASS

FIXED_POLICY_BUY_THRESHOLD = 350


def jail_policy(game: Game, decision: Decision) -> int:
    """Use a card if held; pay early in the game when cash is comfortable; else roll."""
    if JAIL_CARD in decision.legal:
        return JAIL_CARD
    cash = game.state.players[decision.player].cash
    if JAIL_PAY in decision.legal and cash > 500 and game.state.round < 100:
        return JAIL_PAY
    return JAIL_ROLL


class RandomBot:
    name = "random"

    def __init__(self, seed: int | None = None):
        self.rng = random.Random(seed)

    def decide(self, game: Game, decision: Decision) -> int:
        if decision.kind == "jail":
            return jail_policy(game, decision)
        if decision.kind == "buy":
            return BUY if self.rng.random() < 0.5 else PASS
        builds = [a for a in decision.legal if a != PASS]
        return self.rng.choice(builds) if self.rng.random() < 0.5 else PASS


class FixedPolicyBot:
    name = "fixed"

    def __init__(self, threshold: int = FIXED_POLICY_BUY_THRESHOLD):
        self.threshold = threshold

    def decide(self, game: Game, decision: Decision) -> int:
        if decision.kind == "jail":
            return jail_policy(game, decision)
        if game.state.players[decision.player].cash <= self.threshold:
            return PASS
        if decision.kind == "buy":
            return BUY
        # Build on the most expensive buildable group first.
        return max(a for a in decision.legal if a != PASS)


class GreedyBot:
    name = "greedy"

    def decide(self, game: Game, decision: Decision) -> int:
        if decision.kind == "jail":
            return jail_policy(game, decision)
        if decision.kind == "buy":
            return BUY
        return max(decision.legal)


BOTS = {"random": RandomBot, "fixed": FixedPolicyBot, "greedy": GreedyBot}


def make_bot(name: str, seed: int | None = None):
    if name == "random":
        return RandomBot(seed)
    return BOTS[name]()
