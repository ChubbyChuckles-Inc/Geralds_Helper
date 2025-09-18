from __future__ import annotations
from datetime import date
from data.match import Match, aggregate_stats, match_result


def test_aggregate_stats_and_result():
    m1 = Match(
        match_date=date(2025, 3, 1),
        home_team="A",
        away_team="B",
        home_score=5,
        away_score=3,
        completed=True,
    )
    m2 = Match(
        match_date=date(2025, 3, 2),
        home_team="C",
        away_team="D",
        home_score=2,
        away_score=2,
        completed=True,
    )
    m3 = Match(match_date=date(2025, 3, 3), home_team="E", away_team="F")  # incomplete
    stats = aggregate_stats([m1, m2, m3])
    assert (
        stats["total"] == 3
        and stats["completed"] == 2
        and stats["home_wins"] == 1
        and stats["away_wins"] == 0
        and stats["draws"] == 1
    )
    assert match_result(m1) == "5-3"
    assert match_result(m3) == ""
