"""Simple lineup optimization utilities.

Provides basic algorithms to select a lineup of N players from a pool
according to an objective:

- qttr_max: maximize sum of Q-TTR ratings
- balance: minimize rating spread while keeping average high

The goal here is to establish a testable foundation; advanced heuristics
(genetic algorithms, Monte Carlo) can build on this interface later.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Iterable, Sequence, Tuple, Literal
import itertools

from data.player import Player

Objective = Literal["qttr_max", "balance"]


@dataclass
class LineupResult:
    players: List[Player]
    total_qttr: int
    average_qttr: float
    spread: int  # max - min
    objective: Objective

    def to_dict(self):  # pragma: no cover - convenience
        return {
            "players": [p.to_dict() for p in self.players],
            "total_qttr": self.total_qttr,
            "average_qttr": self.average_qttr,
            "spread": self.spread,
            "objective": self.objective,
        }


def _score_balance(lineup: Sequence[Player]) -> Tuple[float, float]:
    ratings = [p.q_ttr for p in lineup]
    spread = max(ratings) - min(ratings)
    avg = sum(ratings) / len(ratings)
    # We prefer lower spread, but not at the cost of drastically lower average.
    # Return tuple with primary=spread, secondary=-average to allow lexicographic min.
    return (spread, -avg)


def optimize_lineup(
    players: Iterable[Player], size: int, objective: Objective = "qttr_max"
) -> LineupResult:
    """Select an optimal lineup.

    Parameters
    ----------
    players: iterable of Player
    size: desired lineup size (>=1)
    objective: "qttr_max" or "balance"

    Returns
    -------
    LineupResult
        Result object containing chosen players and stats.

    Notes
    -----
    Brute-force combination search is used for now. This is fine for
    small rosters (<= 14 choose 6 ~ 3003). Future work: introduce
    pruning/heuristics for larger pools.
    """
    pool = list(players)
    if size <= 0:
        raise ValueError("size must be positive")
    if size > len(pool):
        raise ValueError("size exceeds number of players")

    best_combo = None
    if objective == "qttr_max":
        best_total = -1
        for combo in itertools.combinations(pool, size):
            total = sum(p.q_ttr for p in combo)
            if total > best_total:
                best_total = total
                best_combo = combo
    elif objective == "balance":
        best_key = None
        for combo in itertools.combinations(pool, size):
            key = _score_balance(combo)
            if best_key is None or key < best_key:
                best_key = key
                best_combo = combo
    else:
        raise ValueError(f"Unknown objective: {objective}")

    assert best_combo is not None  # for type checkers
    ratings = [p.q_ttr for p in best_combo]
    total = sum(ratings)
    avg = total / len(ratings)
    spread = max(ratings) - min(ratings)
    return LineupResult(
        players=list(best_combo),
        total_qttr=total,
        average_qttr=avg,
        spread=spread,
        objective=objective,
    )


__all__ = ["optimize_lineup", "LineupResult"]
