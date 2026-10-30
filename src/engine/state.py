"""Mutable game state and action/decision definitions."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

from .board_data import START_CASH, TILES

# Turn-decision actions (shared with Env B's Discrete(10)).
PASS = 0
BUY = 1
BUILD_OFFSET = 1  # build on colour group g (1..8) == action g + 1  -> actions 2..9
N_ACTIONS = 10

# Jail-decision actions.
JAIL_ROLL = 0
JAIL_PAY = 1
JAIL_CARD = 2


def build_action(group: int) -> int:
    return group + BUILD_OFFSET


def action_group(action: int) -> int:
    return action - BUILD_OFFSET


@dataclass
class PlayerState:
    idx: int
    name: str
    cash: int = START_CASH
    position: int = 0
    in_jail: bool = False
    jail_turns: int = 0
    jail_cards: int = 0
    bankrupt: bool = False


@dataclass
class TileState:
    owner: int | None = None
    houses: int = 0
    mortgaged: bool = False


@dataclass
class GameState:
    players: list[PlayerState]
    tiles: list[TileState] = field(default_factory=lambda: [TileState() for _ in TILES])
    first_player: int = 0
    current: int = 0
    round: int = 1
    last_dice: tuple[int, int] = (0, 0)
    finished: bool = False
    winner: int | None = None  # None with finished=True means a draw
    end_reason: str | None = None

    def opponent(self, p: int) -> int:
        return 1 - p

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Decision:
    """A choice the engine is waiting for."""

    kind: str  # "buy" | "build" | "jail"
    player: int
    legal: list[int]
    tile: int | None = None

    def to_dict(self) -> dict:
        return asdict(self)
