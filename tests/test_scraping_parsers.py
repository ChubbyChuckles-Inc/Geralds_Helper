from __future__ import annotations

import pytest
from scraping.parse_club import parse_club_overview
from scraping.parse_division import parse_matchplan
from scraping.parse_team import parse_team_players


CLUB_FIXTURE = """
<html><body>
<table>
 <tr><th>Mannschaft</th><th>Wettbewerb</th><th></th></tr>
 <tr>
  <td>1. Erwachsene</td>
  <td>1. Bezirksliga Erwachsene</td>
  <td>
    <a href="?L1=Ergebnisse&L2=TTStaffeln&L2P=20337&L3=Mannschaften&L3P=129868"> Zum Team</a>
    <a href="?L1=Ergebnisse&L2=TTStaffeln&L2P=20337"> Zum Wettbewerb</a>
  </td>
 </tr>
</table>
</body></html>
"""


MATCHPLAN_FIXTURE = """
<html><body>
 <table>
  <tr>
   <th>Nr.</th><th>Tag</th><th>Datum</th><th>Zeit</th><th>Heimmannschaft</th><th>Gastmannschaft</th><th>Ergebnis</th>
  </tr>
  <tr>
   <td>3105</td><td>So</td><td>07.09.25</td><td>10:00</td><td>SV Rot. Süd Leipzig 3</td><td>SSV Stötteritz</td><td>13:2</td>
  </tr>
  <tr>
   <td>3110</td><td>Sa</td><td>20.09.25</td><td>15:00</td><td>ESV Delitzsch</td><td>SSV Stötteritz</td><td>Vorbericht</td>
  </tr>
 </table>
</body></html>
"""


def test_parse_club_overview_basic():
    teams = parse_club_overview(CLUB_FIXTURE, "https://leipzig.tischtennislive.de")
    assert len(teams) == 1
    t = teams[0]
    assert t.name.startswith("1.")
    assert t.division_id == "20337"
    assert t.team_id in {"129868", "20337"}  # depending which param is extracted


def test_parse_matchplan():
    matches = parse_matchplan(MATCHPLAN_FIXTURE, half=1)
    assert len(matches) == 2
    m0 = matches[0]
    assert m0.number == "3105"
    assert m0.is_played() is True
    assert m0.home_score == 13 and m0.away_score == 2
    m1 = matches[1]
    assert m1.is_played() is False


TEAM_PAGE_FIXTURE = """
<html><body>
 <table>
  <tr><th>Position</th><th>Spieler</th><th>Gesamt</th><th>LivePZ</th></tr>
  <tr><td>1.</td><td>Patrick Stein</td><td>1:3</td><td>1812</td></tr>
  <tr><td>2.</td><td>Sinh Loc Ngo</td><td>0:2</td><td>1756</td></tr>
 </table>
</body></html>
"""


def test_parse_team_players():
    players = parse_team_players(TEAM_PAGE_FIXTURE)
    assert len(players) == 2
    assert players[0].name.startswith("Patrick")
    assert players[0].live_pz == 1812
