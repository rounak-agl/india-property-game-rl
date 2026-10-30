"""Rule-based opponents. Each bot is a Controller: decide(game, decision) -> action."""

from .bots import BOTS, FixedPolicyBot, GreedyBot, RandomBot, jail_policy, make_bot

__all__ = ["BOTS", "FixedPolicyBot", "GreedyBot", "RandomBot", "jail_policy", "make_bot"]
