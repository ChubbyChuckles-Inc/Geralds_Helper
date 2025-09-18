from __future__ import annotations

from src.scraping.parse_division import parse_matchplan

HTML_SNIPPET = """
<table><tbody>
<tr id="Spiel1"><td></td><td>3101</td><td></td><td>Fr</td><td>22.08.25</td><td><span><strong>v</strong></span></td><td>19:00</td><td>TTC Großpösna 1968 2</td><td>TTC Großpösna 1968</td><td align="center"><a>5:10</a></td></tr>
<tr id="Spiel7"><td></td><td>3108</td><td></td><td>Sa</td><td>20.09.25</td><td></td><td>14:00</td><td>Leutzscher Füchse 2</td><td>TTC Großpösna 1968</td><td colspan="2" align="center"><a>Vorbericht</a></td></tr>
</tbody></table>
"""


def test_parse_matchplan_basic():
    matches = parse_matchplan(HTML_SNIPPET, half=1)
    assert len(matches) == 2
    m1, m2 = matches
    assert m1.number == "3101"
    assert m1.date.year == 2025 and m1.date.month == 8 and m1.date.day == 22
    assert m1.time == "19:00"
    assert m1.home == "TTC Großpösna 1968 2"
    assert m1.away == "TTC Großpösna 1968"
    assert m1.home_score == 5 and m1.away_score == 10
    assert m1.is_played()

    assert m2.number == "3108"
    assert m2.result_raw == "Vorbericht"
    assert not m2.is_played()
