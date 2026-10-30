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
