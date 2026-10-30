from src.engine.board_data import BUYABLE_INDICES, GROUP_MEMBERS, TILES
from src.engine.rules import (
    buildable_groups,
    can_build,
    group_build_target,
    raw_net_worth,
    rent_for,
    weighted_net_worth,
)
from src.engine.state import BUY, PASS

MUMBAI, DELHI, GUWAHATI, BHUBANESHWAR = 39, 37, 1, 3


def set_cash(game, player, cash):
    """Change cash while keeping the engine's money-conservation books balanced."""
    game.money_destroyed += game.state.players[player].cash - cash
    game.state.players[player].cash = cash


def own(game, player, *tiles, houses=0):
    for t in tiles:
        game.state.tiles[t].owner = player
        game.state.tiles[t].houses = houses


def test_board_shape():
    assert len(TILES) == 40
    assert len(BUYABLE_INDICES) == 28
    assert {g: len(m) for g, m in GROUP_MEMBERS.items()} == {
        1: 2, 2: 3, 3: 3, 4: 3, 5: 3, 6: 3, 7: 3, 8: 2, 9: 4, 10: 2,
    }


def test_city_rent_base_monopoly_houses_mortgage(make_game):
    g = make_game()
    own(g, 1, MUMBAI)
    assert rent_for(g.state, MUMBAI, 7) == 50
    own(g, 1, DELHI)
    assert rent_for(g.state, MUMBAI, 7) == 100  # unimproved monopoly doubles
    g.state.tiles[MUMBAI].houses = 5
    assert rent_for(g.state, MUMBAI, 7) == 2000
    g.state.tiles[DELHI].mortgaged = True
    assert rent_for(g.state, DELHI, 7) == 0


def test_station_and_utility_rent(make_game):
    g = make_game()
    stations = GROUP_MEMBERS[9]
    for n, expected in enumerate((25, 50, 100, 200), start=1):
        own(g, 1, stations[n - 1])
        assert rent_for(g.state, stations[0], 7) == expected
    own(g, 1, 12)
    assert rent_for(g.state, 12, 8) == 32
    own(g, 1, 28)
    assert rent_for(g.state, 12, 8) == 80


def test_building_requires_monopoly_and_builds_evenly(make_game):
    g = make_game()
    own(g, 0, GUWAHATI)
    assert not can_build(g.state, 0, 1)
    own(g, 0, BHUBANESHWAR)
    assert buildable_groups(g.state, 0) == [1]
    assert group_build_target(g.state, 1) == BHUBANESHWAR  # tie -> higher rent tile
    g.state.tiles[BHUBANESHWAR].houses = 1
    assert group_build_target(g.state, 1) == GUWAHATI
    g.state.tiles[GUWAHATI].mortgaged = True
    assert not can_build(g.state, 0, 1)


def test_hotel_is_the_cap(make_game):
    g = make_game()
    own(g, 0, GUWAHATI, BHUBANESHWAR, houses=5)
    assert group_build_target(g.state, 1) is None
    assert not can_build(g.state, 0, 1)


def test_net_worth(make_game):
    g = make_game()
    own(g, 0, MUMBAI)
    assert raw_net_worth(g.state, 0) == 1500 + 400
    assert weighted_net_worth(g.state, 0) == 1500 + 400 * 1.5
    own(g, 0, DELHI)
    g.state.tiles[MUMBAI].houses = 2
    assert weighted_net_worth(g.state, 0) == 1500 + (400 + 350) * 2.0 + 2 * 200
    g.state.tiles[DELHI].mortgaged = True
    g.state.tiles[MUMBAI].houses = 0
    assert raw_net_worth(g.state, 0) == 1500 + 400 + 175
    assert weighted_net_worth(g.state, 0) == 1500 + 400 * 2.0 + (350 - 175) * 2.0


def test_buy_decision_and_purchase(make_game):
    g = make_game(dice=[1, 2])
    d = g.advance()
    assert d.kind == "buy" and d.tile == BHUBANESHWAR and d.legal == [PASS, BUY]
    g.act(BUY)
    assert g.state.tiles[BHUBANESHWAR].owner == 0
    assert g.state.players[0].cash == 1440


def test_passing_go_pays_salary(make_game):
    g = make_game(dice=[1, 2])
    g.state.players[0].position = 38
    d = g.advance()
    assert d.tile == GUWAHATI
    assert g.state.players[0].cash == 1700


def test_rent_is_transferred(make_game):
    g = make_game(dice=[1, 2])
    own(g, 1, GUWAHATI)
    g.state.players[0].position = 38
    g.advance()
    rent = [e for e in g.events if e.type == "rent_paid"]
    assert rent and rent[0].data["amount"] == 2 and rent[0].data["to"] == 1


def test_go_to_jail_square(make_game):
    g = make_game(dice=[1, 2])
    g.state.players[0].position = 27
    g.advance()
    p = g.state.players[0]
    assert p.in_jail and p.position == 10
    assert any(e.type == "jailed" and e.data["reason"] == "go_to_jail" for e in g.events)


def test_three_doubles_sends_to_jail(make_game):
    g = make_game(dice=[2, 2, 3, 3, 4, 4])
    g.advance()
    jailed = [e for e in g.events if e.type == "jailed"]
    assert jailed and jailed[0].player == 0 and jailed[0].data["reason"] == "three_doubles"
    assert sum(1 for e in g.events if e.type == "dice_rolled" and e.player == 0) == 3


def test_jail_pay_then_normal_turn(make_game):
    from src.engine.state import JAIL_PAY

    g = make_game(dice=[1, 2])
    p = g.state.players[0]
    p.in_jail, p.position = True, 10
    d = g.advance()
    assert d.kind == "jail"
    d = g.act(JAIL_PAY)
    assert p.cash == 1450 and not p.in_jail
    assert d.kind == "buy" and d.tile == BHUBANESHWAR + 10


def test_jail_doubles_leaves_without_extra_roll(make_game):
    from src.engine.state import JAIL_ROLL

    g = make_game(dice=[3, 3])
    p = g.state.players[0]
    p.in_jail, p.position = True, 10
    g.advance()
    d = g.act(JAIL_ROLL)
    assert d.kind == "buy" and d.tile == 16
    g.act(PASS)
    p0_rolls = [e for e in g.events if e.type == "dice_rolled" and e.player == 0]
    assert len(p0_rolls) == 1


def test_third_failed_jail_roll_forces_fine(make_game):
    from src.engine.state import JAIL_ROLL

    g = make_game(dice=[1, 2])
    p = g.state.players[0]
    p.in_jail, p.position, p.jail_turns = True, 10, 2
    g.advance()
    d = g.act(JAIL_ROLL)
    assert p.cash == 1450 and not p.in_jail
    assert d.kind == "buy" and d.tile == 13


def test_bankruptcy_after_liquidation(make_game):
    g = make_game(dice=[1, 2])
    own(g, 1, MUMBAI, DELHI, houses=5)
    own(g, 0, GUWAHATI)
    p0 = g.state.players[0]
    set_cash(g, 0, 10)
    p0.position = 36
    assert g.advance() is None
    assert g.state.finished and g.state.winner == 1 and g.state.end_reason == "bankruptcy"
    assert g.state.players[1].cash == 1500 + 40  # 10 cash + 30 from mortgaging Guwahati
    assert not g.check_invariants()


def test_house_sale_before_mortgage(make_game):
    g = make_game(dice=[1, 2])
    own(g, 0, GUWAHATI, BHUBANESHWAR, houses=1)
    own(g, 1, MUMBAI)
    p0 = g.state.players[0]
    set_cash(g, 0, 30)
    p0.position = 36
    g.advance()
    types = [e.type for e in g.events]
    assert types.index("sold_house") < types.index("rent_paid")
    assert "mortgaged" not in types
    assert not g.check_invariants()


def test_round_limit_ends_game(make_game):
    from src.bots import GreedyBot

    g = make_game(max_rounds=1)
    g.play([GreedyBot(), GreedyBot()])
    assert g.state.finished and g.state.end_reason == "max_rounds"
    assert g.events[-1].type == "game_over"
