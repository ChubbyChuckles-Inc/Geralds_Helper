from __future__ import annotations

from data.player import Player
from analytics.opponent import evaluate_lineups_against_opponent, best_lineup_recommendation
from analytics.sensitivity import weight_spread_sensitivity, best_weight_choice
from analytics.comparison import build_delta_matrix


def _players():
    return [
        Player(name="A", q_ttr=1800, team="T"),
        Player(name="B", q_ttr=1700, team="T"),
        Player(name="C", q_ttr=1600, team="T"),
        Player(name="D", q_ttr=1500, team="T"),
    ]


def test_opponent_analysis():
    pool = _players()
    lineup1 = pool[:3]
    lineup2 = pool[1:4]
    opponent = [
        Player(name="X", q_ttr=1550, team="O"),
        Player(name="Y", q_ttr=1500, team="O"),
        Player(name="Z", q_ttr=1490, team="O"),
    ]
    evals = evaluate_lineups_against_opponent([lineup1, lineup2], opponent)
    assert len(evals) == 2
    rec = best_lineup_recommendation([lineup1, lineup2], opponent)
    assert rec["count_evaluated"] == 2
    assert 0.0 < rec["win_probability"] <= 1.0


def test_weight_spread_sensitivity():
    players = _players()
    weights = [0.2, 0.4, 0.6]
    results = weight_spread_sensitivity(players, size=3, weights=weights)
    assert len(results) == len(weights)
    best = best_weight_choice(results)
    assert best is not None
    # Ensure returned best weight is one of the tested values
    assert best.weight in weights


def test_comparison_delta_matrix():
    labels = ["S1", "S2", "S3"]
    values = [100, 110, 105]
    matrix = build_delta_matrix(labels, values)
    assert len(matrix) == 3 and all(len(r) == 3 for r in matrix)
    # Diagonal should be +0.0
    assert all(matrix[i][i] == "+0.0" for i in range(3))
