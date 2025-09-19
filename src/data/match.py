"""Match data model."""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import List, Optional, Dict, Any
import uuid


@dataclass
class Match:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    match_date: date = field(default_factory=date.today)
    home_team: str = ""
    away_team: str = ""
    location: str = ""
    notes: str = ""
    lineup: List[str] = field(default_factory=list)  # list of player IDs or names (simple for now)
    home_score: int | None = None
    away_score: int | None = None
    completed: bool = False
    report_url: str | None = None  # optional link to online match report / preview

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "match_date": self.match_date.isoformat(),
            "home_team": self.home_team,
            "away_team": self.away_team,
            "location": self.location,
            "notes": self.notes,
            "lineup": list(self.lineup),
            "home_score": self.home_score,
            "away_score": self.away_score,
            "completed": self.completed,
            "report_url": self.report_url,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Match":
        m = cls(
            id=str(data.get("id", str(uuid.uuid4()))),
            match_date=date.fromisoformat(data.get("match_date", date.today().isoformat())),
            home_team=str(data.get("home_team", "")),
            away_team=str(data.get("away_team", "")),
            location=str(data.get("location", "")),
            notes=str(data.get("notes", "")),
        )
        lineup = data.get("lineup", [])
        if isinstance(lineup, list):
            m.lineup.extend(str(x) for x in lineup)
        m.home_score = data.get("home_score")
        m.away_score = data.get("away_score")
        m.completed = bool(data.get("completed", False))
        m.report_url = data.get("report_url")
        return m

    def clone(self) -> "Match":
        return Match.from_dict(self.to_dict())


def detect_conflicts(matches: List[Match]) -> List[tuple[str, str]]:
    """Simple conflict detection: same date and team participates twice."""
    conflicts: List[tuple[str, str]] = []
    by_date: Dict[str, List[Match]] = {}
    for m in matches:
        by_date.setdefault(m.match_date.isoformat(), []).append(m)
    for _d, day_matches in by_date.items():
        for i, a in enumerate(day_matches):
            for b in day_matches[i + 1 :]:
                if (
                    a.home_team == b.home_team
                    or a.home_team == b.away_team
                    or a.away_team == b.home_team
                    or a.away_team == b.away_team
                ):
                    conflicts.append((a.id, b.id))
    return conflicts


def match_result(m: Match) -> str:
    """Return a compact result string or empty if incomplete."""
    if not m.completed or m.home_score is None or m.away_score is None:
        return ""
    return f"{m.home_score}-{m.away_score}"


def aggregate_stats(matches: List[Match]) -> Dict[str, Any]:
    """Compute simple aggregate stats across completed matches.

    Returns dict with keys: total, completed, home_wins, away_wins, draws.
    """
    total = len(matches)
    completed = [
        m for m in matches if m.completed and m.home_score is not None and m.away_score is not None
    ]
    home_wins = sum(1 for m in completed if m.home_score > m.away_score)
    away_wins = sum(1 for m in completed if m.away_score > m.home_score)
    draws = sum(1 for m in completed if m.home_score == m.away_score)
    return {
        "total": total,
        "completed": len(completed),
        "home_wins": home_wins,
        "away_wins": away_wins,
        "draws": draws,
    }


__all__ = ["Match", "detect_conflicts", "match_result", "aggregate_stats"]
