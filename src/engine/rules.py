"""Pure rule functions over GameState. No side effects unless the name says so."""

from __future__ import annotations

from .board_data import (
    COLOR_GROUPS,
    GROUP_MEMBERS,
    MAX_HOUSES,
    STATION_INDICES,
    STATION_RENTS,
    TILES,
    UTILITY_INDICES,
    UTILITY_MULTIPLIERS,
)
from .state import GameState


def owns_group(state: GameState, player: int, group: int) -> bool:
    return all(state.tiles[i].owner == player for i in GROUP_MEMBERS[group])


def owned_tiles(state: GameState, player: int) -> list[int]:
    return [i for i, t in enumerate(state.tiles) if t.owner == player]


def rent_for(state: GameState, idx: int, dice_total: int) -> int:
    """Rent owed for landing on tile `idx` (0 if unowned or mortgaged)."""
    tile, ts = TILES[idx], state.tiles[idx]
    if ts.owner is None or ts.mortgaged:
        return 0
    if tile.kind == "city":
        if ts.houses > 0:
            return tile.rents[ts.houses]
        base = tile.rents[0]
        return base * 2 if owns_group(state, ts.owner, tile.group) else base
    if tile.kind == "station":
        n = sum(1 for i in STATION_INDICES if state.tiles[i].owner == ts.owner)
        return STATION_RENTS[n - 1]
    if tile.kind == "utility":
        n = sum(1 for i in UTILITY_INDICES if state.tiles[i].owner == ts.owner)
        return UTILITY_MULTIPLIERS[n - 1] * dice_total
    return 0


def can_buy(state: GameState, player: int, idx: int) -> bool:
    tile = TILES[idx]
    return (
        tile.buyable
        and state.tiles[idx].owner is None
        and state.players[player].cash >= tile.price
    )


def group_build_target(state: GameState, group: int) -> int | None:
    """Least-developed tile in the group (ties -> highest index, i.e. higher rent)."""
    members = GROUP_MEMBERS[group]
    candidates = [i for i in members if state.tiles[i].houses < MAX_HOUSES]
    if not candidates:
        return None
    return min(candidates, key=lambda i: (state.tiles[i].houses, -i))


def can_build(state: GameState, player: int, group: int) -> bool:
    if group not in COLOR_GROUPS or not owns_group(state, player, group):
        return False
    members = GROUP_MEMBERS[group]
    if any(state.tiles[i].mortgaged for i in members):
        return False
    target = group_build_target(state, group)
    if target is None:
        return False
    return state.players[player].cash >= TILES[target].house_cost


def buildable_groups(state: GameState, player: int) -> list[int]:
    return [g for g in COLOR_GROUPS if can_build(state, player, g)]


def property_value(state: GameState, idx: int) -> int:
    """Liquidation-style value: price (half if mortgaged) + house costs."""
    tile, ts = TILES[idx], state.tiles[idx]
    base = tile.mortgage_value if ts.mortgaged else tile.price
    return base + ts.houses * tile.house_cost


def raw_net_worth(state: GameState, player: int) -> int:
    return state.players[player].cash + sum(property_value(state, i) for i in owned_tiles(state, player))


def weighted_net_worth(
    state: GameState, player: int, b_single: float = 1.5, b_monopoly: float = 2.0
) -> float:
    """Bonjour, Haliem et al. (2022) Eq. 2-3: nw = cash + sum((price - mortgage) * b + houses * cost)."""
    total = float(state.players[player].cash)
    for i in owned_tiles(state, player):
        tile, ts = TILES[i], state.tiles[i]
        owed = tile.mortgage_value if ts.mortgaged else 0
        in_monopoly = tile.group is not None and owns_group(state, player, tile.group)
        b = b_monopoly if in_monopoly else b_single
        total += (tile.price - owed) * b + ts.houses * tile.house_cost
    return total


def liquidation_value(state: GameState, player: int) -> int:
    """Cash the player could raise by selling all houses and mortgaging everything."""
    total = 0
    for i in owned_tiles(state, player):
        tile, ts = TILES[i], state.tiles[i]
        total += ts.houses * tile.house_cost // 2
        if not ts.mortgaged:
            total += tile.mortgage_value
    return total
