import pytest
from optimization.optimizer import optimize_lineup
from data.player import Player


def make_players(ratings):
    return [Player(name=f"P{i}", q_ttr=r) for i, r in enumerate(ratings)]


def test_optimize_qttr_max_simple():
    players = make_players([1000, 1200, 1100, 900])
    res = optimize_lineup(players, size=2, objective="qttr_max")
    chosen = sorted(p.q_ttr for p in res.players)
    assert chosen == [1100, 1200]
    assert res.total_qttr == 2300
    assert res.objective == "qttr_max"


def test_optimize_balance_prefers_lower_spread():
    # Two candidate pairs for size=2:
    # (1000,1400) spread 400 avg 1200 vs (1150,1200) spread 50 avg 1175 => choose second
    players = make_players([1000, 1400, 1150, 1200])
    res = optimize_lineup(players, size=2, objective="balance")
    chosen = sorted(p.q_ttr for p in res.players)
    assert chosen == [1150, 1200]
    assert res.spread == 50


def test_optimize_errors():
    players = make_players([1000, 1100])
    with pytest.raises(ValueError):
        optimize_lineup(players, size=0)
    with pytest.raises(ValueError):
        optimize_lineup(players, size=5)
    with pytest.raises(ValueError):
        optimize_lineup(players, size=1, objective="unknown")
