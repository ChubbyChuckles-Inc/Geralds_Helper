"""Simple in-memory reminder scheduling for matches."""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Callable, Dict, Any
import uuid


@dataclass
class Reminder:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    match_id: str = ""
    when: datetime = field(default_factory=datetime.utcnow)
    message: str = ""
    triggered: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "match_id": self.match_id,
            "when": self.when.isoformat(),
            "message": self.message,
            "triggered": self.triggered,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Reminder":
        r = cls(
            id=str(data.get("id", str(uuid.uuid4()))),
            match_id=str(data.get("match_id", "")),
            when=datetime.fromisoformat(data.get("when", datetime.utcnow().isoformat())),
            message=str(data.get("message", "")),
        )
        r.triggered = bool(data.get("triggered", False))
        return r


class ReminderStore:
    def __init__(self) -> None:
        self._items: List[Reminder] = []

    def schedule(self, *args, **kwargs) -> Reminder:
        """Schedule a reminder.

        Flexible signatures supported for convenience:
        schedule(reminder: Reminder)
        schedule(when: datetime, message: str, match_id: str = "")
        """
        if args and isinstance(args[0], Reminder):  # direct reminder
            reminder = args[0]
        else:
            if not args:
                raise TypeError("schedule requires a Reminder or (when, message[, match_id])")
            when = args[0]
            try:
                message = args[1]
            except IndexError:  # pragma: no cover - defensive
                raise TypeError(
                    "schedule requires message when using (when, message[, match_id]) form"
                )
            match_id = args[2] if len(args) > 2 else kwargs.get("match_id", "")
            reminder = Reminder(match_id=match_id, when=when, message=message)
        self._items.append(reminder)
        return reminder

    def due(self, now: datetime | None = None, reference: datetime | None = None) -> List[Reminder]:
        # allow "reference" alias for clarity in tests
        ts = reference or now or datetime.utcnow()
        return [r for r in self._items if not r.triggered and r.when <= ts]

    def mark_triggered(self, reminder_id: str) -> None:
        for r in self._items:
            if r.id == reminder_id:
                r.triggered = True
                break

    def all(self) -> List[Reminder]:
        return [r for r in self._items]


__all__ = ["Reminder", "ReminderStore"]
