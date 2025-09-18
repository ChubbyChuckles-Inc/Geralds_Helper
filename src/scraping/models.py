"""Data models for structured scraping results.

These models intentionally keep only normalized identifiers so we can later
persist or map them into existing domain objects (e.g. Match -> data.match.Match).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import List, Optional
import re


@dataclass(slots=True)
class ClubTeam:
    """Represents a team row from the club overview page."""

    name: str
    division_name: str
    team_url: str  # relative href to team details ("Zum Team")
    division_url: str  # relative href to division overview/entry ("Zum Wettbewerb")
    division_id: Optional[str] = None  # extracted L2P
    team_id: Optional[str] = None  # extracted L3P or similar if available

    def derive_ids(self) -> None:
        if self.division_id is None:
            self.division_id = _extract_query_param(self.division_url, "L2P")
        if self.team_id is None:
            self.team_id = _extract_query_param(self.team_url, "L3P") or _extract_query_param(
                self.team_url, "L2P"
            )


@dataclass(slots=True)
class DivisionTeam:
    name: str
    team_url: Optional[str] = None
    team_id: Optional[str] = None

    def derive_ids(self) -> None:
        if self.team_url and self.team_id is None:
            self.team_id = _extract_query_param(self.team_url, "L3P") or _extract_query_param(
                self.team_url, "L2P"
            )


@dataclass(slots=True)
class ScheduledMatch:
    """Represents a single scheduled (or completed) match from a Spielplan table."""

    number: str  # Nr. column
    date: date
    time: str  # keep as raw HH:MM or placeholder (some rows show 'v 19:00')
    home: str
    away: str
    result_raw: str  # keep raw text like '5:10', 'Vorbericht', ''
    half: int  # 1 = Vorrunde, 2 = Rückrunde
    home_score: int | None = None
    away_score: int | None = None
    # Optional single-letter status flag found between date and time cells (e.g. 'v', 't')
    status_flag: str | None = (
        None  # e.g. 'v' (verlegt/postponed), 't' (Tausch?) single-letter markers
    )
    # Link (relative) to the official match report or preview page (Spielbericht). For future
    # matches this still points to the preview 'Vorbericht' page, once played it contains score.
    match_report_url: str | None = None

    def is_played(self) -> bool:
        if self.home_score is not None and self.away_score is not None:
            return True
        return bool(re.match(r"^\d+:\d+", self.result_raw))

    def parse_scores(self) -> None:
        m = re.match(r"^(\d+):(\d+)", self.result_raw)
        if m:
            self.home_score = int(m.group(1))
            self.away_score = int(m.group(2))


@dataclass(slots=True)
class Division:
    name: str
    division_id: str
    season: str
    teams: List[DivisionTeam] = field(default_factory=list)
    matches: List[ScheduledMatch] = field(default_factory=list)

    def add_team(self, t: DivisionTeam) -> None:
        self.teams.append(t)

    def add_match(self, m: ScheduledMatch) -> None:
        self.matches.append(m)


def _extract_query_param(href: str, key: str) -> Optional[str]:
    pattern = re.compile(rf"[?&]{key}=([^&#]+)")
    m = pattern.search(href)
    if m:
        return m.group(1)
    return None


__all__ = [
    "ClubTeam",
    "DivisionTeam",
    "ScheduledMatch",
    "Division",
]
