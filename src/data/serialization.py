"""Serialization utilities for players (JSON & CSV)."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Iterable, List

from .player import Player


def save_players_json(players: Iterable[Player], path: Path) -> None:
    data = [p.to_dict() for p in players]
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_players_json(path: Path) -> list[Player]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return [Player.from_dict(obj) for obj in data]


def save_players_csv(players: Iterable[Player], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "name", "team", "q_ttr"])
        for p in players:
            w.writerow([p.id, p.name, p.team or "", p.q_ttr])


def load_players_csv(path: Path) -> list[Player]:
    out: list[Player] = []
    with path.open("r", newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            out.append(
                Player(
                    name=row.get("name", ""),
                    q_ttr=int(row.get("q_ttr", 0)),
                    team=row.get("team") or None,
                    id=row.get("id") or None,  # type: ignore[arg-type]
                )
            )
    return out


__all__ = [
    "save_players_json",
    "load_players_json",
    "save_players_csv",
    "load_players_csv",
]
