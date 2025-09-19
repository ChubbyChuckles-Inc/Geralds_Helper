"""What-if scenario batch optimization helpers.

Provides a function to run multiple scenarios where each scenario can
exclude (treat as unavailable) a list of player IDs and returns
ScenarioResult objects with scenario_name set.
"""

from __future__ import annotations
from typing import Iterable, List, Sequence, Dict
from datetime import date

from data.player import Player
from .optimizer import optimize_lineup, Objective
from .scenario import ScenarioResult


def run_what_if_scenarios(
    players: Sequence[Player],
    scenarios: Sequence[Dict],
    size: int,
    objective: Objective = "qttr_max",
    availability_date: str | None = None,
    start_id: int = 1,
) -> List[ScenarioResult]:
    """Run multiple what-if scenarios.

    Each scenario dict may contain:
      - name: str (label)
      - exclude_ids: list[str] player IDs to treat as unavailable
      - exclude_names: list[str] player names (case-insensitive) alternative

    availability_date: if provided (ISO), only players whose availability
    set is empty OR contains the date are considered before exclusions.
    """
    results: List[ScenarioResult] = []
    current_id = start_id
    for sc in scenarios:
        label = str(sc.get("name", f"Scenario {current_id}"))
        exclude_ids = {str(x) for x in sc.get("exclude_ids", [])}
        exclude_names_lc = {str(x).lower() for x in sc.get("exclude_names", [])}
        # Filter by availability first
        pool: List[Player] = []
        for p in players:
            if availability_date and p.availability and availability_date not in p.availability:
                continue
            if p.id in exclude_ids or p.name.lower() in exclude_names_lc:
                continue
            pool.append(p)
        if len(pool) < size:
            # Skip scenario if not enough players; still record placeholder
            dummy = ScenarioResult(
                id=current_id,
                timestamp="1970-01-01T00:00:00",
                objective=objective,
                size=size,
                total_qttr=0,
                average_qttr=0.0,
                spread=0,
                players=[],
                scenario_name=label + " (insufficient players)",
            )
            results.append(dummy)
            current_id += 1
            continue
        lr = optimize_lineup(pool, size=size, objective=objective)
        sr = ScenarioResult.from_lineup(current_id, size=size, result=lr)
        sr.scenario_name = label
        results.append(sr)
        current_id += 1
    return results


__all__ = ["run_what_if_scenarios"]
