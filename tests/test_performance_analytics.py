from __future__ import annotations

from data.player import Player
from analytics.performance import compute_rating_trend, team_strength_snapshot
from optimization.prediction import predict_match_outcome


def test_compute_rating_trend_basic():
    p1 = Player(name="Alpha", q_ttr=1600)
    p1.history = [("2025-01-01", 1500), ("2025-02-01", 1550), ("2025-03-01", 1600)]
    p2 = Player(name="Beta", q_ttr=1400)
    p2.history = [("2025-02-01", 1410)]  # single point
    trends = compute_rating_trend([p1, p2])
    t1 = trends[p1.id]
    assert t1.recent_delta == 50
    assert round(t1.slope, 1) == 50.0
    t2 = trends[p2.id]
    assert t2.slope == 0.0 and t2.recent_delta == 0


def test_team_strength_snapshot_and_prediction():
    a = [Player(name="A1", q_ttr=1700), Player(name="A2", q_ttr=1650)]
    b = [Player(name="B1", q_ttr=1500), Player(name="B2", q_ttr=1520)]
    snap_a = team_strength_snapshot(a)
    snap_b = team_strength_snapshot(b)
    assert snap_a["avg"] > snap_b["avg"]
    outcome = predict_match_outcome(a, b)
    assert 0.5 < outcome["team_a_win"] < 1.0
    assert abs(outcome["team_a_win"] + outcome["team_b_win"] - 1.0) < 1e-9
