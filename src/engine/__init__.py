"""Pure-Python game engine (no RL, web or torch imports)."""

from .board_data import TILES
from .engine import Controller, Event, Game, IllegalAction
from .state import Decision, GameState

__all__ = ["TILES", "Controller", "Decision", "Event", "Game", "GameState", "IllegalAction"]
