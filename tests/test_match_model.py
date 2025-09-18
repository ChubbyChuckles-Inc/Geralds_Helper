from __future__ import annotations
from datetime import date
from data.match import Match, detect_conflicts


def test_match_serialization_and_conflict():
    m1 = Match(match_date=date(2025, 1, 1), home_team="A", away_team="B")
    m2 = Match(match_date=date(2025, 1, 1), home_team="A", away_team="C")
    d = [m1.to_dict(), m2.to_dict()]
    r1 = Match.from_dict(d[0])
    r2 = Match.from_dict(d[1])
    conflicts = detect_conflicts([r1, r2])
    assert conflicts and isinstance(conflicts[0], tuple)


def test_match_result_serialization():
    m = Match(match_date=date(2025, 2, 2), home_team="Alpha", away_team="Beta")
    m.home_score = 9
    m.away_score = 7
    m.completed = True
    d = m.to_dict()
    clone = Match.from_dict(d)
    assert clone.home_score == 9 and clone.away_score == 7 and clone.completed is True
