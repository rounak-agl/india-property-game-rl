"""Observation encoders (TECH_SPEC §4.2-4.3). Pure functions of (state, agent seat, decision)."""

from __future__ import annotations

import numpy as np

from src.engine.board_data import BUYABLE_INDICES, COLOR_GROUPS, TILES
from src.engine.rules import buildable_groups
from src.engine.state import Decision, GameState

OBS_A_SIZE = 32
OBS_B_SIZE = 133


def encode_a(state: GameState, agent: int) -> np.ndarray:
    """Blueprint 32-dim vector: positions, cash, and 28 property owner codes."""
    opp = 1 - agent
    me, them = state.players[agent], state.players[opp]
    obs = [me.position / 39, them.position / 39, min(me.cash / 2000, 5.0), min(them.cash / 2000, 5.0)]
    for i in BUYABLE_INDICES:
        ts = state.tiles[i]
        if ts.owner is None:
            obs.append(0.0)
        elif ts.owner == agent:
            obs.append(2.0 if ts.houses > 0 else 1.0)
        else:
            obs.append(-1.0)
    return np.asarray(obs, dtype=np.float32)


def encode_b(state: GameState, agent: int, decision: Decision | None, nw_share: float) -> np.ndarray:
    """Rich 133-dim vector, all values in [0, 1]."""
    obs: list[float] = []
    for seat, share in ((agent, nw_share), (1 - agent, 1.0 - nw_share)):
        pl = state.players[seat]
        obs += [pl.position / 39, min(pl.cash / 3000, 1.0), float(pl.in_jail), min(pl.jail_cards, 1), share]
    for i in BUYABLE_INDICES:
        ts = state.tiles[i]
        obs += [float(ts.owner == agent), float(ts.owner == 1 - agent), ts.houses / 5, float(ts.mortgaged)]
    kind = decision.kind if decision else None
    tile_price = TILES[decision.tile].price / 400 if decision and decision.tile is not None else 0.0
    buildable = set(buildable_groups(state, agent)) if kind == "build" else set()
    obs += [float(kind == "buy"), float(kind == "build"), tile_price]
    obs += [float(g in buildable) for g in COLOR_GROUPS]
    return np.asarray(obs, dtype=np.float32)
