from __future__ import annotations

from pathlib import Path
from src.scraping.parse_division import parse_matchplan

FIXTURE = Path("tests/fixtures/matchplan_vorrunde.html")


def test_parse_matchplan_full_fixture():
    html = FIXTURE.read_text(encoding="utf-8")
    matches = parse_matchplan(html)  # half auto-detected
    # We only embedded 5 rows (subset) in the fixture for regression focus
    assert len(matches) == 5
    # First row (played match)
    m1 = matches[0]
    assert m1.number == "3101"
    assert m1.home == "TTC Großpösna 1968 2"
    assert m1.away == "TTC Großpösna 1968"
    assert m1.home_score == 5 and m1.away_score == 10
    assert m1.match_report_url and "Spielbericht" in m1.match_report_url
    assert m1.status_flag == "v"
    assert m1.half == 1
    # Row with plain score (second)
    m2 = matches[1]
    assert m2.result_raw == "9:6"
    # Vorbericht future row (third)
    m3 = matches[2]
    assert m3.result_raw == "Vorbericht"
    assert m3.home_score is None and m3.away_score is None
    # Row with status 't'
    m4 = matches[3]
    assert m4.status_flag == "t"
    assert m4.result_raw == "Vorbericht"
    # Last embedded row
    m5 = matches[4]
    assert m5.number == "3145"
    assert m5.result_raw == "Vorbericht"
