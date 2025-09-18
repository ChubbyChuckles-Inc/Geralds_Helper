"""High-level scraping orchestration functions."""

from __future__ import annotations

from urllib.parse import urlparse, parse_qs, urlencode
from dataclasses import dataclass
from typing import Dict, List

from .fetch import Fetcher, SupportsGet
from .parse_club import parse_club_overview
from .parse_division import parse_matchplan, parse_division_teams
from .models import ClubTeam, Division
from .parse_team import parse_team_players


@dataclass
class ClubScrapeResult:
    club_url: str
    teams: list[ClubTeam]
    divisions: dict[str, Division]  # key = division_id
    team_players: dict[str, list] | None = None  # key team_id -> list[TeamPlayerStat]


def scrape_club(
    club_overview_url: str,
    fetcher: SupportsGet | None = None,
    *,
    include_team_players: bool = True,
) -> ClubScrapeResult:
    fetcher = fetcher or Fetcher(throttle=0.5)
    base_url = _derive_base(club_overview_url)
    html = fetcher.get(club_overview_url)
    club_teams = parse_club_overview(html, base_url)

    divisions: dict[str, Division] = {}
    for ct in club_teams:
        if not ct.division_id:
            continue
        if ct.division_id not in divisions:
            divisions[ct.division_id] = Division(
                name=ct.division_name,
                division_id=ct.division_id,
                season=_extract_season_from_url(club_overview_url) or "",
            )
    # Fetch match plans and teams for each division once
    for div_id, div in divisions.items():
        # Spielplan half 1 & 2
        for half in (1, 2):
            url = _build_division_matchplan_url(div_id, half, base_url)
            try:
                mhtml = fetcher.get(url)
            except Exception:  # pragma: no cover - network failure path
                continue
            matches = parse_matchplan(mhtml, half)
            for m in matches:
                div.add_match(m)
        # Teams list (if not present we can attempt the 'Mannschaften' page)
        # Usually the division root page is the one referenced in the club table (div_url)
        sample_team_url = _build_division_root_url(div_id, base_url)
        try:
            dhtml = fetcher.get(sample_team_url)
            teams = parse_division_teams(dhtml)
            for t in teams:
                # avoid duplicates
                if all(existing.name != t.name for existing in div.teams):
                    div.add_team(t)
        except Exception:  # pragma: no cover
            pass

    team_players: dict[str, list] | None = None
    if include_team_players:
        team_players = {}
        for ct in club_teams:
            if not ct.team_url or not ct.team_id:
                continue
            try:
                thtml = fetcher.get(ct.team_url)
            except Exception:  # pragma: no cover
                continue
            players = parse_team_players(thtml)
            if players:
                team_players[ct.team_id] = players

    return ClubScrapeResult(
        club_url=club_overview_url,
        teams=club_teams,
        divisions=divisions,
        team_players=team_players,
    )


def _derive_base(url: str) -> str:
    p = urlparse(url)
    return f"{p.scheme}://{p.netloc}"


def _extract_season_from_url(url: str) -> str | None:
    q = parse_qs(urlparse(url).query)
    # site uses Saison=2025 maybe
    vals = q.get("Saison")
    return vals[0] if vals else None


def _build_division_matchplan_url(division_id: str, half: int, base_url: str) -> str:
    # Example: ?L1=Ergebnisse&L2=TTStaffeln&L2P=20337&L3=Spielplan&L3P=1
    query = {
        "L1": "Ergebnisse",
        "L2": "TTStaffeln",
        "L2P": division_id,
        "L3": "Spielplan",
        "L3P": str(half),
    }
    return f"{base_url}/?{urlencode(query)}"


def _build_division_root_url(division_id: str, base_url: str) -> str:
    # Root division page (Übersicht/tab) may just omit L3; replicate minimal query
    query = {"L1": "Ergebnisse", "L2": "TTStaffeln", "L2P": division_id}
    return f"{base_url}/?{urlencode(query)}"


__all__ = ["scrape_club", "ClubScrapeResult"]
