"""Player data model."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Dict, Any, Set
import uuid


@dataclass
class Player:
    """Represents a player with Q-TTR rating and history.

    Attributes
    ----------
    id: str
        Stable unique identifier (UUID4).
    name: str
        Player full name.
    team: str | None
        Team code or name.
    q_ttr: int
        Current Q-TTR rating.
    history: list[tuple[str, int]]
        Tuples of (ISO date, q_ttr) for rating evolution.
    """

    name: str
    q_ttr: int
    team: str | None = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    history: List[tuple[str, int]] = field(default_factory=list)
    availability: Set[str] = field(default_factory=set)  # ISO date strings when available
    photo_path: str | None = None

    def add_history_point(self, rating: int, when: datetime | None = None) -> None:
        when = when or datetime.now(timezone.utc)
        self.history.append((when.date().isoformat(), rating))
        self.q_ttr = rating

    # Availability management
    def toggle_availability(self, date_iso: str) -> None:
        if date_iso in self.availability:
            self.availability.remove(date_iso)
        else:
            self.availability.add(date_iso)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "team": self.team,
            "q_ttr": self.q_ttr,
            "history": list(self.history),
            "availability": sorted(self.availability),
            "photo_path": self.photo_path,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Player":
        p = cls(
            name=str(data["name"]),
            q_ttr=int(data["q_ttr"]),
            team=data.get("team"),
            id=str(data.get("id", str(uuid.uuid4()))),
        )
        history = data.get("history", [])
        if isinstance(history, list):
            p.history.extend([(str(d), int(r)) for d, r in history])
        avail = data.get("availability", [])
        if isinstance(avail, list):
            p.availability.update(str(d) for d in avail)
        p.photo_path = data.get("photo_path") or None
        return p

    def clone(self) -> "Player":
        return Player.from_dict(self.to_dict())


__all__ = ["Player"]
