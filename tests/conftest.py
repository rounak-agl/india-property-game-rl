import random

import pytest

from src.engine import Game


class ScriptedRandom(random.Random):
    """Returns scripted dice values first, then falls back to normal randomness."""

    def __init__(self, dice: list[int], seed: int = 0):
        super().__init__(seed)
        self.dice = list(dice)

    def randint(self, a, b):
        if self.dice and (a, b) == (1, 6):
            return self.dice.pop(0)
        return super().randint(a, b)


@pytest.fixture
def make_game():
    def _make(dice: list[int] | None = None, first_player: int = 0, **kwargs) -> Game:
        game = Game(seed=0, first_player=first_player, **kwargs)
        game.rng = ScriptedRandom(dice or [])
        return game

    return _make
