import pytest

from src.bots import make_bot
from src.engine import Game, IllegalAction


def test_same_seed_same_game():
    def run():
        g = Game(seed=7)
        g.play([make_bot("random", 1), make_bot("fixed")])
        return [(e.type, e.player, e.data) for e in g.events]

    assert run() == run()


def test_illegal_action_rejected():
    g = Game(seed=1)
    d = g.advance()
    with pytest.raises(IllegalAction):
        g.act(99)
    assert g.pending is d


def test_act_without_pending_decision_rejected():
    g = Game(seed=1)
    with pytest.raises(IllegalAction):
        g.act(0)


@pytest.mark.parametrize("pair", [("random", "random"), ("greedy", "fixed"), ("random", "greedy")])
def test_soak_invariants(pair):
    for seed in range(1000):
        g = Game(seed=seed)
        decision = g.advance()
        bots = [make_bot(pair[0], seed), make_bot(pair[1], seed + 1)]
        while decision is not None:
            decision = g.act(bots[decision.player].decide(g, decision))
            errors = g.check_invariants()
            assert not errors, (seed, errors)
        assert g.state.finished


def test_blueprint_mode_asks_every_move_and_treats_invalid_as_pass():
    from src.bots import FixedPolicyBot

    class AlwaysBuild:
        def decide(self, game, decision):
            return 2 if decision.kind == "turn" else 0

    g = Game(seed=3, blueprint_players={0})
    g.play([AlwaysBuild(), FixedPolicyBot()])
    turn_decisions = sum(1 for e in g.events if e.type == "moved" and e.player == 0)
    assert turn_decisions > 0
    assert not any(e.type == "bought" and e.player == 0 for e in g.events)
    assert not g.check_invariants()


def test_blueprint_mode_soak():
    from src.bots import RandomBot

    class RandomTurn:
        def __init__(self, seed):
            import random

            self.rng = random.Random(seed)

        def decide(self, game, decision):
            return self.rng.choice(decision.legal)

    for seed in range(300):
        g = Game(seed=seed, blueprint_players={0})
        g.play([RandomTurn(seed), RandomBot(seed)])
        assert g.state.finished and not g.check_invariants()
