from __future__ import annotations

import pytest

from optimization.optimizer import optimize_lineup, LineupResult
from data.player import Player


def _players():
    # create a spread of ratings so weighted can differ from qttr_max
    return [
        Player(name="A", q_ttr=1800, team="T"),
        Player(name="B", q_ttr=1750, team="T"),
        Player(name="C", q_ttr=1500, team="T"),
        Player(name="D", q_ttr=1490, team="T"),
        Player(name="E", q_ttr=1480, team="T"),
    ]


def test_weighted_objective_prefers_lower_spread():
    players = _players()
    # qttr_max with size 3 should pick A,B,C (total=5050 spread=300)
    r_max = optimize_lineup(players, size=3, objective="qttr_max")
    assert {p.name for p in r_max.players} == {"A", "B", "C"}
    # weighted should potentially drop C for D to reduce spread depending on weight
    r_weighted = optimize_lineup(players, size=3, objective="weighted", weight_spread=0.6)
    assert r_weighted.objective == "weighted"
    # Ensure spread is reduced vs pure max (or equal if tie) while total not catastrophically low
    assert r_weighted.spread <= r_max.spread
    assert r_weighted.total_qttr >= r_max.total_qttr - 200


def test_reasoning_and_warnings_fields():
    players = _players()
    r = optimize_lineup(players, size=3, objective="weighted", weight_spread=0.5)
    assert r.reasoning and "objective=weighted" in r.reasoning
    assert isinstance(r.warnings, list)


def test_ga_path(monkeypatch):
    players = _players() + [
        Player(name="F", q_ttr=1470, team="T"),
        Player(name="G", q_ttr=1460, team="T"),
        Player(name="H", q_ttr=1450, team="T"),
    ]
    # Force GA by setting low threshold
    r = optimize_lineup(
        players,
        size=4,
        objective="qttr_max",
        ga_threshold=10,
        ga_generations=5,
        ga_population=12,
        random_seed=1,
    )
    assert r.reasoning and "objective=qttr_max" in r.reasoning
    # GA usage should have heuristic warning
    assert "heuristic_ga" in (r.warnings or [])
