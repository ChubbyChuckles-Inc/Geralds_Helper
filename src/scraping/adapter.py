"""High-level convenience functions bridging scraping layer and GUI.

Provides simplified APIs:
- get_club_teams(base_url, club_html_path=None)
- get_team_players(base_url, team, team_html_path=None)

These wrap lower-level fetch + parse utilities and convert results to GUI `Player` models.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional
import logging
import requests

from .parse_club import parse_club_overview  # type: ignore
from .parse_team import parse_team_players
from .parse_division import parse_matchplan
from .models import ClubTeam, ScheduledMatch
from data.player import Player
from data.match import Match

log = logging.getLogger(__name__)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125 Safari/537.36"


def _fetch(url: str) -> str:
    resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=20)
    resp.raise_for_status()
    return resp.text


def get_club_teams(base_url: str, *, club_html_path: Path | None = None) -> List[ClubTeam]:
    """Retrieve club teams either from offline HTML or live network.

    Parameters
    ----------
    base_url: str
        Full URL to the club page listing teams.
    club_html_path: Optional[Path]
        If provided, read HTML from path instead of network.
    """
    if club_html_path and club_html_path.exists():
        html = club_html_path.read_text(encoding="utf-8")
    else:
        html = _fetch(base_url)
    teams = parse_club_overview(html, base_url)
    log.info("Parsed %d club teams", len(teams))
    return teams


def get_team_players(
    base_url: str, team: ClubTeam, *, team_html_path: Path | None = None
) -> List[Player]:
    """Retrieve players for a single club team.

    If offline file is provided it is used; else we request the resolved absolute team URL.
    """
    # Derive absolute team URL
    if team.team_url.startswith("http"):
        team_url = team.team_url
    else:
        # naive join (site uses relative root '/?query')
        if base_url.endswith("/"):
            base_root = base_url.rstrip("/")
        else:
            base_root = base_url
        # We only need domain root; heuristic: split at '/?' first occurrence
        import urllib.parse

        parsed = urllib.parse.urlparse(base_root)
        domain_root = f"{parsed.scheme}://{parsed.netloc}"
        team_url = domain_root + team.team_url
    if team_html_path and team_html_path.exists():
        html = team_html_path.read_text(encoding="utf-8")
    else:
        html = _fetch(team_url)
    stats = parse_team_players(html)
    players: List[Player] = []
    for s in stats:
        rating = s.live_pz if s.live_pz is not None else 1200
        p = Player(name=s.name, q_ttr=rating, team=team.name)
        players.append(p)
    log.info("Parsed %d players for team %s", len(players), team.name)
    return players


def _absolute_url(base_url: str, rel: str) -> str:
    if rel.startswith("http"):
        return rel
    import urllib.parse

    parsed = urllib.parse.urlparse(base_url)
    domain_root = f"{parsed.scheme}://{parsed.netloc}"
    return domain_root + rel


def get_division_schedule(
    base_url: str, team: ClubTeam, *, division_html_path: Path | None = None
) -> List[Match]:
    """Fetch division schedule and convert to Match objects.

    Currently parses a single division page (both halves if present)."""
    if not team.division_url:
        raise ValueError("ClubTeam.division_url missing; cannot import schedule")
    division_url = _absolute_url(base_url, team.division_url)
    if division_html_path and division_html_path.exists():
        html = division_html_path.read_text(encoding="utf-8")
    else:
        html = _fetch(division_url)
    scheduled: List[ScheduledMatch] = parse_matchplan(html, half=None)
    matches: List[Match] = []
    for sm in scheduled:
        m = Match(
            match_date=sm.date,
            home_team=sm.home,
            away_team=sm.away,
            notes=f"Half {sm.half}" + (f" | {sm.status_flag}" if sm.status_flag else ""),
        )
        if sm.match_report_url:
            m.report_url = _absolute_url(base_url, sm.match_report_url)
        if sm.home_score is not None and sm.away_score is not None:
            m.home_score = sm.home_score
            m.away_score = sm.away_score
            m.completed = True
        matches.append(m)
    log.info("Converted %d scheduled matches", len(matches))
    return matches


__all__ = ["get_club_teams", "get_team_players", "get_division_schedule"]
