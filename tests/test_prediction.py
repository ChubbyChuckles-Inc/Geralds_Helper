from __future__ import annotations

from data.player import Player
from optimization.prediction import logistic_win_probability, monte_carlo_match


def _team(ratings):
    return [Player(name=f"P{i}", q_ttr=r, team="T") for i, r in enumerate(ratings)]


def test_logistic_probability_symmetry():
    team_a = _team([1800, 1750, 1700])
    team_b = _team([1700, 1650, 1600])
    p_ab = logistic_win_probability(team_a, team_b)
    p_ba = logistic_win_probability(team_b, team_a)
    assert 0.5 < p_ab < 1.0
    # Symmetry: p(a beats b) ~= 1 - p(b beats a)
    assert abs(p_ab - (1 - p_ba)) < 1e-9


def test_monte_carlo_match_stats():
    team_a = _team([1600, 1600, 1600])
    team_b = _team([1500, 1500, 1500])
    stats = monte_carlo_match(team_a, team_b, iterations=500, random_seed=42)
    assert stats.n == 500
    assert 0 < stats.wins < 500
    # Empirical should be close to theoretical probability (within ~10%) for 500 trials
    assert abs(stats.empirical_p - stats.win_probability_mean) < 0.1
