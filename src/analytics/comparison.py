"""Comparative analysis matrix utilities.

Generates pairwise delta matrices for a numeric metric across scenarios.
"""

from __future__ import annotations

from typing import Sequence, Dict, List, Callable


def build_delta_matrix(labels: Sequence[str], values: Sequence[float]) -> List[List[str]]:
    if len(labels) != len(values):  # pragma: no cover - defensive
        raise ValueError("labels and values length mismatch")
    n = len(values)
    matrix: List[List[str]] = []
    for i in range(n):
        row: List[str] = []
        for j in range(n):
            delta = values[j] - values[i]
            row.append(f"{delta:+.1f}")
        matrix.append(row)
    return matrix


def matrix_to_markdown(labels: Sequence[str], matrix: Sequence[Sequence[str]]) -> str:
    header = "| Scenario | " + " | ".join(labels) + " |"
    sep = "|" + "---|" * (len(labels) + 1)
    lines = [header, sep]
    for label, row in zip(labels, matrix):
        lines.append("| " + label + " | " + " | ".join(row) + " |")
    return "\n".join(lines)


__all__ = ["build_delta_matrix", "matrix_to_markdown"]
