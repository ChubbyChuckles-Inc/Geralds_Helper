"""Sensitivity analysis utilities for optimization parameters."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence, List, Dict

from data.player import Player
from optimization.optimizer import optimize_lineup


@dataclass
class WeightSpreadResult:
    weight: float
    total_qttr: int
    spread: int
    score: float
    players: List[str]


def weight_spread_sensitivity(
    players: Iterable[Player],
    size: int,
    weights: Sequence[float],
) -> List[WeightSpreadResult]:
    results: List[WeightSpreadResult] = []
    for w in weights:
        r = optimize_lineup(players, size=size, objective="weighted", weight_spread=w)
        score = r.total_qttr - w * r.spread
        results.append(
            WeightSpreadResult(
                weight=w,
                total_qttr=r.total_qttr,
                spread=r.spread,
                score=score,
                players=[p.name for p in r.players],
            )
        )
    return results


def best_weight_choice(results: Sequence[WeightSpreadResult]) -> WeightSpreadResult | None:
    if not results:
        return None
    return max(results, key=lambda r: r.score)


__all__ = ["weight_spread_sensitivity", "best_weight_choice", "WeightSpreadResult"]
