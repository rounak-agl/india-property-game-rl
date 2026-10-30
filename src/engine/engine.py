"""Turn-based game engine for two players.

The game is a generator-driven state machine: `advance()` runs the game until a
player has to decide something and returns that `Decision`; `act(action)` answers
it. RL environments, bots, the API and humans all drive the same engine this way.
"""

from __future__ import annotations

import random
from collections.abc import Collection, Generator, Sequence
from dataclasses import asdict, dataclass, field
from typing import Protocol

from .board_data import (
    GO_SALARY,
    GROUP_MEMBERS,
    JAIL_FINE,
    JAIL_INDEX,
    MAX_HOUSES,
    START_CASH,
    STATION_INDICES,
    TILES,
    UTILITY_INDICES,
)
from .cards import CHANCE_CARDS, CHEST_CARDS, Card, Deck
from .rules import (
    buildable_groups,
    can_buy,
    group_build_target,
    owned_tiles,
    owns_group,
    raw_net_worth,
    rent_for,
)
from .state import (
    BUY,
    JAIL_CARD,
    JAIL_PAY,
    JAIL_ROLL,
    PASS,
    Decision,
    GameState,
    PlayerState,
    action_group,
    build_action,
)

DEFAULT_MAX_ROUNDS = 200

Flow = Generator[Decision, int, None]


class IllegalAction(ValueError):
    pass


@dataclass
class Event:
    seq: int
    round: int
    player: int | None
    type: str
    data: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


class Controller(Protocol):
    def decide(self, game: Game, decision: Decision) -> int: ...


class Game:
    def __init__(
        self,
        seed: int | None = None,
        names: Sequence[str] = ("Player 1", "Player 2"),
        first_player: int | None = None,
        max_rounds: int = DEFAULT_MAX_ROUNDS,
        blueprint_players: Collection[int] = (),
        pause_each_turn: bool = False,
    ):
        """`blueprint_players` get one Pass/Buy/Build "turn" decision after every move
        instead of separate buy and build decisions (Env A, faithful to the blueprint).
        `pause_each_turn` yields a "next_turn" decision (only legal action: 0) before every
        turn, so a UI can replay the game one turn at a time."""
        self.rng = random.Random(seed)
        if first_player is None:
            first_player = self.rng.randrange(2)
        players = [PlayerState(i, names[i]) for i in range(2)]
        self.state = GameState(players=players, first_player=first_player, current=first_player)
        self.max_rounds = max_rounds
        self.blueprint_players = frozenset(blueprint_players)
        self.pause_each_turn = pause_each_turn
        self.decks = {"chance": Deck(CHANCE_CARDS, self.rng), "chest": Deck(CHEST_CARDS, self.rng)}
        self.jail_card_sources: dict[int, list[str]] = {0: [], 1: []}
        self.events: list[Event] = []
        self.money_created = 0
        self.money_destroyed = 0
        self.pending: Decision | None = None
        self._gen: Flow = self._play()
        self._started = False

    # ------------------------------------------------------------------ driving
    @property
    def finished(self) -> bool:
        return self.state.finished

    def advance(self) -> Decision | None:
        """Run until the next decision (returned) or the end of the game (None)."""
        if self.pending is not None or self.state.finished:
            return self.pending
        self._resume(None)
        return self.pending

    def act(self, action: int) -> Decision | None:
        """Answer the pending decision and run until the next one."""
        if self.pending is None:
            raise IllegalAction("no decision is pending")
        if action not in self.pending.legal:
            raise IllegalAction(f"action {action} not legal for {self.pending}")
        self.pending = None
        self._resume(action)
        return self.pending

    def play(self, controllers: Sequence[Controller]) -> int | None:
        """Play to the end with one controller per seat. Returns the winner (None = draw)."""
        decision = self.advance()
        while decision is not None:
            decision = self.act(controllers[decision.player].decide(self, decision))
        return self.state.winner

    def _resume(self, value: int | None) -> None:
        try:
            if not self._started:
                self._started = True
                self.pending = next(self._gen)
            else:
                self.pending = self._gen.send(value)  # type: ignore[arg-type]
        except StopIteration:
            self.pending = None

    # ------------------------------------------------------------------ flow
    def _play(self) -> Flow:
        s = self.state
        self._emit("game_start", None, first_player=s.first_player, names=[p.name for p in s.players])
        while True:
            yield from self._turn(s.current)
            if s.finished:
                return
            s.current = s.opponent(s.current)
            if s.current == s.first_player:
                if s.round >= self.max_rounds:
                    self._end_by_net_worth()
                    return
                s.round += 1

    def _turn(self, p: int) -> Flow:
        s, pl = self.state, self.state.players[p]
        if self.pause_each_turn:
            yield Decision("next_turn", p, [0])
        self._emit("turn_start", p)
        if pl.in_jail:
            result = yield from self._jail_phase(p)
            if s.finished:
                return
            if result is None:
                yield from self._blueprint_turn(p)
                return
            if result != "free":
                total = sum(result)
                self._move_by(p, total)
                yield from self._resolve_landing(p, total)
                yield from self._blueprint_turn(p)
                return
        doubles = 0
        while True:
            yield from self._build_phase(p)
            if s.finished:
                return
            d1, d2 = self._roll(p)
            if d1 == d2:
                doubles += 1
                if doubles == 3:
                    self._send_to_jail(p, "three_doubles")
                    yield from self._blueprint_turn(p)
                    return
            self._move_by(p, d1 + d2)
            yield from self._resolve_landing(p, d1 + d2)
            yield from self._blueprint_turn(p)
            if s.finished or pl.in_jail or d1 != d2:
                return

    def _blueprint_turn(self, p: int) -> Flow:
        """Env A: one Pass(0) / Buy(1) / Build(2) choice per move; invalid choices act as Pass."""
        s = self.state
        if p not in self.blueprint_players or s.finished:
            return
        idx = s.players[p].position
        action = yield Decision("turn", p, [0, 1, 2], tile=idx)
        if action == 1 and can_buy(s, p, idx):
            self._buy(p, idx)
            return
        if action == 2:
            groups = buildable_groups(s, p)
            if groups:
                # The owned monopoly with the fewest houses; ties -> more expensive group.
                g = min(groups, key=lambda g: (sum(s.tiles[i].houses for i in GROUP_MEMBERS[g]), -g))
                self._build(p, g)
                return
        if TILES[idx].buyable and s.tiles[idx].owner is None:
            self._emit("declined", p, tile=idx, reason="choice")

    def _jail_phase(self, p: int) -> Generator[Decision, int, tuple[int, int] | str | None]:
        s, pl = self.state, self.state.players[p]
        legal = [JAIL_ROLL]
        if pl.cash >= JAIL_FINE:
            legal.append(JAIL_PAY)
        if pl.jail_cards > 0:
            legal.append(JAIL_CARD)
        action = yield Decision("jail", p, legal)
        if action == JAIL_CARD:
            pl.jail_cards -= 1
            deck = self.jail_card_sources[p].pop()
            self.decks[deck].return_jail_card()
            self._leave_jail(p, "card")
            return "free"
        if action == JAIL_PAY:
            self._pay_bank(p, JAIL_FINE, "jail_fine")
            if s.finished:
                return None
            self._leave_jail(p, "paid")
            return "free"
        d1, d2 = self._roll(p)
        if d1 == d2:
            self._leave_jail(p, "doubles")
            return (d1, d2)
        pl.jail_turns += 1
        if pl.jail_turns >= 3:
            self._pay_bank(p, JAIL_FINE, "jail_fine")
            if s.finished:
                return None
            self._leave_jail(p, "forced_fine")
            return (d1, d2)
        self._emit("stayed_in_jail", p, attempts=pl.jail_turns)
        return None

    def _build_phase(self, p: int) -> Flow:
        s = self.state
        if p in self.blueprint_players:
            return
        while not s.finished:
            groups = buildable_groups(s, p)
            if not groups:
                return
            action = yield Decision("build", p, [PASS] + [build_action(g) for g in groups])
            if action == PASS:
                return
            self._build(p, action_group(action))

    def _resolve_landing(self, p: int, dice_total: int) -> Flow:
        s, pl = self.state, self.state.players[p]
        idx = pl.position
        tile, ts = TILES[idx], s.tiles[idx]
        if tile.buyable:
            if ts.owner is None:
                if p in self.blueprint_players:
                    pass  # decided in _blueprint_turn
                elif can_buy(s, p, idx):
                    action = yield Decision("buy", p, [PASS, BUY], tile=idx)
                    if action == BUY:
                        self._buy(p, idx)
                    else:
                        self._emit("declined", p, tile=idx, reason="choice")
                else:
                    self._emit("declined", p, tile=idx, reason="cash")
            elif ts.owner != p:
                rent = rent_for(s, idx, dice_total)
                if rent > 0:
                    self._pay_player(p, ts.owner, rent, "rent", tile=idx)
                else:
                    self._emit("no_rent", p, tile=idx, reason="mortgaged")
        elif tile.kind == "tax":
            self._pay_bank(p, tile.tax, "tax", tile=idx)
        elif tile.kind == "goto_jail":
            self._send_to_jail(p, "go_to_jail")
        elif tile.kind in ("chance", "chest"):
            yield from self._draw_card(p, tile.kind, dice_total)

    def _draw_card(self, p: int, deck: str, dice_total: int) -> Flow:
        s, pl = self.state, self.state.players[p]
        card: Card = self.decks[deck].draw()
        self._emit("card_drawn", p, deck=deck, card_id=card.id, text=card.text)
        kind, *args = card.effect
        opp = s.opponent(p)
        if kind == "collect":
            self._bank_pays(p, args[0], "card")
        elif kind == "pay":
            self._pay_bank(p, args[0], "card")
        elif kind == "advance":
            self._move_to(p, args[0])
            yield from self._resolve_landing(p, dice_total)
        elif kind == "nearest":
            targets = STATION_INDICES if args[0] == "station" else UTILITY_INDICES
            target = min(targets, key=lambda t: (t - pl.position) % 40 or 40)
            self._move_to(p, target)
            yield from self._resolve_landing(p, dice_total)
        elif kind == "back":
            self._move_back(p, args[0])
            yield from self._resolve_landing(p, dice_total)
        elif kind == "jail":
            self._send_to_jail(p, "card")
        elif kind == "jail_card":
            pl.jail_cards += 1
            self.jail_card_sources[p].append(deck)
        elif kind == "repairs":
            per_house, per_hotel = args
            amount = 0
            for i in owned_tiles(s, p):
                h = s.tiles[i].houses
                amount += per_hotel if h == MAX_HOUSES else per_house * h
            if amount:
                self._pay_bank(p, amount, "repairs")
        elif kind == "pay_opponent":
            self._pay_player(p, opp, args[0], "card")
        elif kind == "collect_from_opponent":
            self._pay_player(opp, p, args[0], "card")

    # ------------------------------------------------------------------ actions
    def _roll(self, p: int) -> tuple[int, int]:
        dice = (self.rng.randint(1, 6), self.rng.randint(1, 6))
        self.state.last_dice = dice
        self._emit("dice_rolled", p, dice=list(dice), total=sum(dice), doubles=dice[0] == dice[1])
        return dice

    def _move_by(self, p: int, steps: int) -> None:
        pl = self.state.players[p]
        start = pl.position
        path = [(start + i) % 40 for i in range(1, steps + 1)]
        pl.position = path[-1]
        self._emit("moved", p, frm=start, to=pl.position, path=path)
        if start + steps >= 40:
            self._bank_pays(p, GO_SALARY, "passed_go")

    def _move_to(self, p: int, target: int) -> None:
        steps = (target - self.state.players[p].position) % 40 or 40
        self._move_by(p, steps)

    def _move_back(self, p: int, steps: int) -> None:
        pl = self.state.players[p]
        start = pl.position
        path = [(start - i) % 40 for i in range(1, steps + 1)]
        pl.position = path[-1]
        self._emit("moved", p, frm=start, to=pl.position, path=path)

    def _send_to_jail(self, p: int, reason: str) -> None:
        pl = self.state.players[p]
        pl.position, pl.in_jail, pl.jail_turns = JAIL_INDEX, True, 0
        self._emit("jailed", p, reason=reason)

    def _leave_jail(self, p: int, method: str) -> None:
        pl = self.state.players[p]
        pl.in_jail, pl.jail_turns = False, 0
        self._emit("left_jail", p, method=method)

    def _buy(self, p: int, idx: int) -> None:
        tile = TILES[idx]
        self.state.players[p].cash -= tile.price
        self.money_destroyed += tile.price
        self.state.tiles[idx].owner = p
        self._emit("bought", p, tile=idx, price=tile.price,
                   completes_group=tile.group is not None and owns_group(self.state, p, tile.group))

    def _build(self, p: int, group: int) -> None:
        idx = group_build_target(self.state, group)
        assert idx is not None
        cost = TILES[idx].house_cost
        self.state.players[p].cash -= cost
        self.money_destroyed += cost
        self.state.tiles[idx].houses += 1
        self._emit("built", p, tile=idx, group=group, houses=self.state.tiles[idx].houses, cost=cost)

    # ------------------------------------------------------------------ money
    def _bank_pays(self, p: int, amount: int, reason: str) -> None:
        self.state.players[p].cash += amount
        self.money_created += amount
        self._emit("collected", p, amount=amount, reason=reason)

    def _pay_bank(self, p: int, amount: int, reason: str, **data) -> None:
        pl = self.state.players[p]
        if not self._raise_cash(p, amount):
            self.money_destroyed += pl.cash
            pl.cash = 0
            self._bankrupt(p, creditor=None, owed=amount)
            return
        pl.cash -= amount
        self.money_destroyed += amount
        self._emit("tax_paid" if reason == "tax" else "paid", p, amount=amount, to=None, reason=reason, **data)

    def _pay_player(self, p: int, to: int, amount: int, reason: str, **data) -> None:
        payer, payee = self.state.players[p], self.state.players[to]
        if not self._raise_cash(p, amount):
            payee.cash += payer.cash
            payer.cash = 0
            self._bankrupt(p, creditor=to, owed=amount)
            return
        payer.cash -= amount
        payee.cash += amount
        self._emit("rent_paid" if reason == "rent" else "paid", p, amount=amount, to=to, reason=reason, **data)

    def _raise_cash(self, p: int, needed: int) -> bool:
        """Forced liquidation: sell houses (half cost), then mortgage cheapest tiles."""
        s, pl = self.state, self.state.players[p]
        while pl.cash < needed:
            with_houses = [i for i in owned_tiles(s, p) if s.tiles[i].houses > 0]
            if not with_houses:
                break
            i = max(with_houses, key=lambda i: (TILES[i].house_cost, s.tiles[i].houses, i))
            s.tiles[i].houses -= 1
            gain = TILES[i].house_cost // 2
            pl.cash += gain
            self.money_created += gain
            self._emit("sold_house", p, tile=i, houses=s.tiles[i].houses, amount=gain)
        while pl.cash < needed:
            free = [i for i in owned_tiles(s, p) if not s.tiles[i].mortgaged]
            if not free:
                break
            i = min(free, key=lambda i: (TILES[i].price, i))
            s.tiles[i].mortgaged = True
            gain = TILES[i].mortgage_value
            pl.cash += gain
            self.money_created += gain
            self._emit("mortgaged", p, tile=i, amount=gain)
        return pl.cash >= needed

    # ------------------------------------------------------------------ ending
    def _bankrupt(self, p: int, creditor: int | None, owed: int) -> None:
        s = self.state
        s.players[p].bankrupt = True
        for ts in s.tiles:
            if ts.owner == p:
                ts.owner, ts.houses, ts.mortgaged = None, 0, False
        self._emit("bankrupt", p, creditor=creditor, owed=owed)
        self._finish(s.opponent(p), "bankruptcy")

    def _end_by_net_worth(self) -> None:
        nw = [raw_net_worth(self.state, i) for i in range(2)]
        winner = None if nw[0] == nw[1] else (0 if nw[0] > nw[1] else 1)
        self._finish(winner, "max_rounds", net_worth=nw)

    def _finish(self, winner: int | None, reason: str, **data) -> None:
        s = self.state
        s.finished, s.winner, s.end_reason = True, winner, reason
        self._emit("game_over", None, winner=winner, reason=reason, **data)

    def log_event(self, type_: str, player: int | None, **data) -> None:
        """Add an external event (e.g. an AI "decision" explanation) to the game log."""
        self._emit(type_, player, **data)

    def _emit(self, type_: str, player: int | None, **data) -> None:
        self.events.append(Event(len(self.events), self.state.round, player, type_, data))

    # ------------------------------------------------------------------ checks
    def check_invariants(self) -> list[str]:
        s, errors = self.state, []
        expected = 2 * START_CASH + self.money_created - self.money_destroyed
        if sum(pl.cash for pl in s.players) != expected:
            errors.append(f"money not conserved: {sum(pl.cash for pl in s.players)} != {expected}")
        for pl in s.players:
            if pl.cash < 0:
                errors.append(f"player {pl.idx} has negative cash {pl.cash}")
            if not 0 <= pl.position < 40:
                errors.append(f"player {pl.idx} off board")
            if pl.in_jail and pl.position != JAIL_INDEX:
                errors.append(f"player {pl.idx} jailed but not on jail tile")
        for i, ts in enumerate(s.tiles):
            tile = TILES[i]
            if ts.owner is not None and not tile.buyable:
                errors.append(f"tile {i} is not buyable but owned")
            if not 0 <= ts.houses <= MAX_HOUSES:
                errors.append(f"tile {i} has {ts.houses} houses")
            if ts.houses and (tile.kind != "city" or ts.owner is None or not owns_group(s, ts.owner, tile.group)):
                errors.append(f"tile {i} has houses without a monopoly")
            if ts.mortgaged and ts.houses:
                errors.append(f"tile {i} mortgaged with houses")
        return errors
