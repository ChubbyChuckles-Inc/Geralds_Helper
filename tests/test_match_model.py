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
