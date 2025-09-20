"""Simple performance prediction models.

Provides:
 - logistic_win_probability(team_a, team_b): probability team_a beats team_b
 - monte_carlo_match(team_a, team_b, n): simulate outcomes returning stats

Assumptions:
 Each player contributes additively via Q-TTR; team rating = sum.
 Home advantage / contextual factors not yet modeled.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence, Dict
import math
import random

from data.player import Player


def team_rating(players: Iterable[Player]) -> int:
    return sum(p.q_ttr for p in players)


def logistic_win_probability(
    team_a: Sequence[Player], team_b: Sequence[Player], scale: float = 400.0
) -> float:
    """Compute win probability using logistic model similar to Elo.

    P(A wins) = 1 / (1 + 10 ^ ((R_b - R_a)/scale))
    """
    ra = team_rating(team_a)
    rb = team_rating(team_b)
    exponent = (rb - ra) / scale
    return 1.0 / (1.0 + math.pow(10.0, exponent))


@dataclass
class SimulationStats:
    n: int
    wins: int
    losses: int
    win_probability_mean: float
    empirical_p: float

    def to_dict(self):  # pragma: no cover - convenience
        return {
            "n": self.n,
            "wins": self.wins,
            "losses": self.losses,
            "win_probability_mean": self.win_probability_mean,
            "empirical_p": self.empirical_p,
        }


def monte_carlo_match(
    team_a: Sequence[Player],
    team_b: Sequence[Player],
    iterations: int = 2000,
    random_seed: int | None = 1234,
) -> SimulationStats:
    """Run Monte Carlo Bernoulli trials based on logistic probability.

    Returns counts and empirical probability for validation / reporting.
    """
    if iterations <= 0:
        raise ValueError("iterations must be positive")
    p = logistic_win_probability(team_a, team_b)
    rng = random.Random(random_seed)
    wins = 0
    for _ in range(iterations):
        if rng.random() < p:
            wins += 1
    losses = iterations - wins
    empirical = wins / iterations
    return SimulationStats(
        n=iterations,
        wins=wins,
        losses=losses,
        win_probability_mean=p,
        empirical_p=empirical,
    )


__all__ = [
    "logistic_win_probability",
    "monte_carlo_match",
    "SimulationStats",
]
