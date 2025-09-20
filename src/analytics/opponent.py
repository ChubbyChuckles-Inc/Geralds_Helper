"""Opponent analysis utilities.

Provides helper to evaluate multiple candidate lineups against an opponent
roster using existing prediction facilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence, List, Dict

from data.player import Player
from optimization.prediction import predict_match_outcome


@dataclass
class LineupEvaluation:
    lineup: List[str]  # player names
    win_probability: float
    rating_diff: float

    def to_row(self) -> List[str]:  # pragma: no cover - presentation helper
        return [",".join(self.lineup), f"{self.win_probability:.3f}", f"{self.rating_diff:.0f}"]


def evaluate_lineups_against_opponent(
    candidate_lineups: Sequence[Sequence[Player]], opponent: Sequence[Player]
) -> List[LineupEvaluation]:
    results: List[LineupEvaluation] = []
    for lineup in candidate_lineups:
        outcome = predict_match_outcome(lineup, opponent)
        results.append(
            LineupEvaluation(
                lineup=[p.name for p in lineup],
                win_probability=outcome["team_a_win"],
                rating_diff=outcome["rating_diff"],
            )
        )
    # Sort descending by win probability then rating diff
    results.sort(key=lambda x: (x.win_probability, x.rating_diff), reverse=True)
    return results


def best_lineup_recommendation(
    candidate_lineups: Sequence[Sequence[Player]], opponent: Sequence[Player]
) -> Dict[str, object]:
    evals = evaluate_lineups_against_opponent(candidate_lineups, opponent)
    if not evals:
        return {"lineup": [], "win_probability": 0.0, "rating_diff": 0.0}
    top = evals[0]
    return {
        "lineup": top.lineup,
        "win_probability": top.win_probability,
        "rating_diff": top.rating_diff,
        "count_evaluated": len(evals),
    }


__all__ = [
    "evaluate_lineups_against_opponent",
    "best_lineup_recommendation",
    "LineupEvaluation",
]
