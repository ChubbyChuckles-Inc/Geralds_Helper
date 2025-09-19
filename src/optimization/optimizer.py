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
from typing import List, Iterable, Sequence, Tuple, Literal, Optional
import itertools
import random

from data.player import Player

Objective = Literal["qttr_max", "balance", "weighted"]


def _nCr(n: int, r: int) -> int:
    """Compute combinations n choose r (small n) without math.comb.

    Implemented manually to avoid Python version dependency and allow
    early stopping patterns if needed later.
    """
    if r < 0 or r > n:
        return 0
    r = min(r, n - r)
    numer = 1
    denom = 1
    for i in range(1, r + 1):
        numer *= n - (r - i)
        denom *= i
    return numer // denom


@dataclass
class LineupResult:
    players: List[Player]
    total_qttr: int
    average_qttr: float
    spread: int  # max - min
    objective: Objective
    reasoning: Optional[str] = None
    warnings: List[str] = None  # type: ignore

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
    players: Iterable[Player],
    size: int,
    objective: Objective = "qttr_max",
    weight_spread: float = 0.3,
    ga_threshold: int = 5000,
    ga_generations: int = 60,
    ga_population: int = 40,
    random_seed: Optional[int] = 42,
) -> LineupResult:
    """Select an optimal lineup.

    Parameters
    ----------
    players: iterable of Player
    size: desired lineup size (>=1)
    objective: "qttr_max", "balance", or "weighted"
    weight_spread: (weighted) total - weight_spread * spread scoring factor
    ga_threshold: use GA heuristic if combinations exceed this value

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

    total_combos = _nCr(len(pool), size)
    use_ga = total_combos > ga_threshold
    rng = random.Random(random_seed)
    best_combo = None
    if not use_ga:
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
        elif objective == "weighted":
            best_score = None
            for combo in itertools.combinations(pool, size):
                ratings = [p.q_ttr for p in combo]
                score = sum(ratings) - weight_spread * (max(ratings) - min(ratings))
                if best_score is None or score > best_score:
                    best_score = score
                    best_combo = combo
        else:
            raise ValueError(f"Unknown objective: {objective}")
    else:
        # Simple GA heuristic for large search spaces
        indices = list(range(len(pool)))

        def fitness(ids: Sequence[int]) -> float:
            lineup = [pool[i] for i in ids]
            rs = [p.q_ttr for p in lineup]
            total = sum(rs)
            spread = max(rs) - min(rs)
            if objective == "qttr_max":
                return float(total)
            if objective == "balance":
                return 10_000 - spread * 10 + (total / len(rs))
            return total - weight_spread * spread  # weighted

        population: List[Tuple[List[int], float]] = []
        while len(population) < ga_population:
            ids = sorted(rng.sample(indices, size))
            population.append((ids, fitness(ids)))
        for _ in range(ga_generations):
            population.sort(key=lambda x: x[1], reverse=True)
            survivors = population[: max(2, ga_population // 2)]
            children: List[Tuple[List[int], float]] = []
            while len(survivors) + len(children) < ga_population:
                a, b = rng.sample(survivors, 2)
                cut = rng.randint(1, size - 1)
                child = sorted(list(dict.fromkeys(a[0][:cut] + b[0][cut:])))
                while len(child) < size:
                    cand = rng.choice(indices)
                    if cand not in child:
                        child.append(cand)
                        child.sort()
                if rng.random() < 0.2:
                    # mutation swap one id
                    swap_index = rng.randrange(size)
                    new_id = rng.choice([i for i in indices if i not in child])
                    child[swap_index] = new_id
                    child.sort()
                children.append((child, fitness(child)))
            population = survivors + children
        population.sort(key=lambda x: x[1], reverse=True)
        best_combo = [pool[i] for i in population[0][0]]

    assert best_combo is not None  # for type checkers
    ratings = [p.q_ttr for p in best_combo]
    total = sum(ratings)
    avg = total / len(ratings)
    spread = max(ratings) - min(ratings)
    reasoning_parts = [f"objective={objective}"]
    if objective == "weighted":
        reasoning_parts.append(f"weight_spread={weight_spread}")
    reasoning_parts.append(f"players={','.join(p.name for p in best_combo)}")
    reasoning_parts.append(f"total={total} avg={avg:.1f} spread={spread}")
    warnings: List[str] = []
    if spread > 250:
        warnings.append("high_spread")
    if use_ga:
        warnings.append("heuristic_ga")
    return LineupResult(
        players=list(best_combo),
        total_qttr=total,
        average_qttr=avg,
        spread=spread,
        objective=objective,
        reasoning=";".join(reasoning_parts),
        warnings=warnings,
    )


__all__ = ["optimize_lineup", "LineupResult"]
