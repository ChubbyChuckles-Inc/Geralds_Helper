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


ALT_TEAM_PAGE_FIXTURE = """
<html><body>
 <table>
  <tbody>
  <tr class="ui-widget-header"><td></td><td align="right">Pos</td><td></td><td>Spieler</td><td>Kennz</td><td align="right">ST</td><td align="center">PK1</td><td align="center">PK2</td><td align="center">PK3</td><td align="center">Gesamt</td><td align="right">LivePZ</td><td></td></tr>
  <tr id="Spieler_129868_1"><td></td><td align="right">1.</td><td></td><td><a href="?L1=E&L2=TT&L3=Spieler&L3P=114277">Patrick Stein</a></td><td></td><td align="right">1</td><td align="center">0:2</td><td></td><td></td><td align="center">0:2</td><td align="right">1812</td><td></td></tr>
  <tr id="Spieler_129868_2"><td></td><td align="right">2.</td><td></td><td><a href="?L1=E&L2=TT&L3=Spieler&L3P=121975">Sinh Loc Ngo</a></td><td></td><td></td><td></td><td></td><td></td><td></td><td align="right">1756</td><td></td></tr>
  <tr id="Spieler_129868_3"><td></td><td align="right">3.</td><td></td><td><a href="?L1=E&L2=TT&L3=Spieler&L3P=134146">Sarah Uecker</a></td><td></td><td align="right">1</td><td align="center">1:1</td><td></td><td></td><td align="center">1:1</td><td align="right">1760</td><td></td></tr>
  <tr class="ui-widget-header"><td></td><td></td><td></td><td colspan="3">Gesamt</td><td align="center">1:3</td><td align="center">0:4</td><td align="center">1:3</td><td align="center">2:10</td><td></td><td></td></tr>
  </tbody>
 </table>
</body></html>
"""


def test_parse_team_players_alternate_layout():
    players = parse_team_players(ALT_TEAM_PAGE_FIXTURE)
    # Should parse at least 3 players before the summary row
    assert len(players) >= 3
    names = [p.name for p in players]
    assert any("Patrick" in n for n in names)
    # Ratings should include 1812 and 1756
    ratings = {p.live_pz for p in players if p.live_pz}
    assert 1812 in ratings and 1756 in ratings
