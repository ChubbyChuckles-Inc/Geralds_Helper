"""Conversion helpers from scraping models to core data models."""

from __future__ import annotations

from typing import Iterable, List
from data.match import Match
from .models import ScheduledMatch


def scheduled_to_matches(scheduled: Iterable[ScheduledMatch]) -> list[Match]:
    out: list[Match] = []
    for sm in scheduled:
        m = Match(
            match_date=sm.date,
            home_team=sm.home,
            away_team=sm.away,
            notes=f"Half {sm.half} | Source #{sm.number}",
        )
        if sm.home_score is not None and sm.away_score is not None:
            m.home_score = sm.home_score
            m.away_score = sm.away_score
            m.completed = True
        out.append(m)
    return out


__all__ = ["scheduled_to_matches"]
