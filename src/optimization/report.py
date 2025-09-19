"""Optimization reporting utilities.

Generates a markdown report for a set of ScenarioResult entries including
summary statistics (best / worst totals, average, spread distribution) and
an ASCII bar chart (pure text) so we avoid extra plotting dependencies.
"""

from __future__ import annotations
from typing import Sequence
from statistics import mean
from .scenario import ScenarioResult


def build_report(history: Sequence[ScenarioResult]) -> str:
    if not history:
        return "# Optimization Report\n\n_No scenarios available to report._\n"
    totals = [h.total_qttr for h in history]
    spreads = [h.spread for h in history]
    best_total = max(totals)
    worst_total = min(totals)
    avg_total = mean(totals)
    avg_spread = mean(spreads)
    lines = ["# Optimization Report", ""]
    lines.append("## Summary")
    lines.append(f"Scenarios: {len(history)}")
    lines.append(f"Best Total: {best_total}")
    lines.append(f"Worst Total: {worst_total}")
    lines.append(f"Average Total: {avg_total:.1f}")
    lines.append(f"Average Spread: {avg_spread:.1f}")
    lines.append("")
    lines.append("## Totals Bar Chart (ASCII)")
    scale = max(1, best_total)
    # Normalize to 40 chars width
    for h in history:
        width = int((h.total_qttr / scale) * 40)
        label = h.scenario_name or f"Scenario {h.id}"
        lines.append(f"{label:20} | {'#' * width} {h.total_qttr}")
    lines.append("")
    lines.append("## Detailed Scenarios")
    lines.append(
        "| ID | Time | Objective | Size | Total | Avg | Spread | Delta | Scenario | Lineup |"
    )
    lines.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    # Recompute best reference per objective (qttr_max highest, others lowest)
    best_ref_max = max((h.total_qttr for h in history if h.objective == "qttr_max"), default=None)
    best_ref_min = min((h.total_qttr for h in history if h.objective != "qttr_max"), default=None)
    for h in history:
        if h.objective == "qttr_max":
            delta = "" if best_ref_max is None else h.total_qttr - best_ref_max
        else:
            delta = "" if best_ref_min is None else h.total_qttr - best_ref_min
        lineup = ", ".join(p["name"] for p in h.players)
        lines.append(
            f"| {h.id} | {h.timestamp.split('T')[-1]} | {h.objective} | {h.size} | {h.total_qttr} | {h.average_qttr:.1f} | {h.spread} | {delta} | {h.scenario_name or ''} | {lineup} |"
        )
    return "\n".join(lines) + "\n"


__all__ = ["build_report"]
