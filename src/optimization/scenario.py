"""Scenario tracking and export helpers for optimization results."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List
from datetime import datetime
from optimization.optimizer import LineupResult


@dataclass
class ScenarioResult:
    id: int
    timestamp: str
    objective: str
    size: int
    total_qttr: int
    average_qttr: float
    spread: int
    players: list[dict]

    @classmethod
    def from_lineup(cls, ident: int, size: int, result: LineupResult) -> "ScenarioResult":
        return cls(
            id=ident,
            timestamp=datetime.utcnow().isoformat(timespec="seconds"),
            objective=result.objective,
            size=size,
            total_qttr=result.total_qttr,
            average_qttr=result.average_qttr,
            spread=result.spread,
            players=[p.to_dict() for p in result.players],
        )

    def to_row(self, best_total: int | None = None) -> list[str]:  # for table display
        delta = "" if best_total is None else str(self.total_qttr - best_total)
        return [
            str(self.id),
            self.timestamp.split("T")[-1],
            self.objective,
            str(self.size),
            str(self.total_qttr),
            f"{self.average_qttr:.1f}",
            str(self.spread),
            delta,
        ]


def export_markdown(history: List[ScenarioResult]) -> str:
    lines = ["# Optimization Scenarios Report", ""]
    lines.append("| ID | Time (UTC) | Objective | Size | Total | Avg | Spread | Lineup |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- | --- |")
    for s in history:
        lineup = ", ".join(p["name"] for p in s.players)
        lines.append(
            f"| {s.id} | {s.timestamp} | {s.objective} | {s.size} | {s.total_qttr} | {s.average_qttr:.1f} | {s.spread} | {lineup} |"
        )
    return "\n".join(lines) + "\n"


__all__ = ["ScenarioResult", "export_markdown"]
