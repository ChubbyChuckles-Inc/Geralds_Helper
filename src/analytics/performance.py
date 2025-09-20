"""Performance analytics utilities.

Currently provides:
 - compute_rating_trend(players): slope & recent delta per player
 - team_strength_snapshot(players): aggregate rating stats

Design goals:
 - Pure functions for easy unit testing.
 - No external dependencies beyond stdlib.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Dict, List
from statistics import mean

from data.player import Player


@dataclass
class RatingTrend:
    name: str
    current: int
    recent_delta: int
    history_points: int
    slope: float  # simple average delta per step

    def to_row(self) -> List[str]:  # pragma: no cover - presentation helper
        return [
            self.name,
            str(self.current),
            str(self.recent_delta),
            f"{self.slope:.1f}",
            str(self.history_points),
        ]


def compute_rating_trend(players: Iterable[Player]) -> Dict[str, RatingTrend]:
    """Compute a naive slope based on successive history differences.

    If fewer than 2 history points, slope=0 and recent_delta=0.
    """
    results: Dict[str, RatingTrend] = {}
    for p in players:
        hist = p.history
        if len(hist) < 2:
            results[p.id] = RatingTrend(
                name=p.name,
                current=p.q_ttr,
                recent_delta=0,
                history_points=len(hist),
                slope=0.0,
            )
            continue
        ratings = [r for _d, r in hist]
        deltas = [b - a for a, b in zip(ratings, ratings[1:])]
        slope = mean(deltas) if deltas else 0.0
        recent_delta = deltas[-1] if deltas else 0
        results[p.id] = RatingTrend(
            name=p.name,
            current=p.q_ttr,
            recent_delta=recent_delta,
            history_points=len(hist),
            slope=slope,
        )
    return results


def team_strength_snapshot(players: Iterable[Player]) -> Dict[str, float]:
    arr = [p.q_ttr for p in players]
    if not arr:
        return {"count": 0, "avg": 0.0, "min": 0.0, "max": 0.0}
    return {
        "count": float(len(arr)),
        "avg": float(mean(arr)),
        "min": float(min(arr)),
        "max": float(max(arr)),
    }


__all__ = ["compute_rating_trend", "team_strength_snapshot", "RatingTrend"]
