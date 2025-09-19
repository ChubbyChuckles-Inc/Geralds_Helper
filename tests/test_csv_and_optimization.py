from __future__ import annotations

from pathlib import Path
from data.player import Player
from data.serialization import save_players_csv, load_players_csv
from optimization.scenario import ScenarioResult
from optimization.optimizer import LineupResult


def test_players_csv_round_trip(tmp_path: Path):
    players = [
        Player(name="Alice", q_ttr=1500, team="A"),
        Player(name="Bob", q_ttr=1600, team="B"),
    ]
    csv_path = tmp_path / "players.csv"
    save_players_csv(players, csv_path)
    loaded = load_players_csv(csv_path)
    assert len(loaded) == 2
    names = {p.name for p in loaded}
    assert names == {"Alice", "Bob"}
    # ensure availability preserved (add one, re-save)
    players[0].availability.add("2025-09-19")
    save_players_csv(players, csv_path)
    loaded2 = load_players_csv(csv_path)
    avail_counts = {p.name: len(p.availability) for p in loaded2}
    assert avail_counts["Alice"] == 1


def _fake_lineup_result(objective: str, total: int, avg: float, spread: int, players: list[Player]):
    # Minimal shim for LineupResult interface used in ScenarioResult.from_lineup
    class _LR:
        def __init__(self):
            self.objective = objective
            self.total_qttr = total
            self.average_qttr = avg
            self.spread = spread
            self.players = players

    return _LR()


def test_scenario_best_delta():
    p1 = Player(name="A", q_ttr=1500)
    p2 = Player(name="B", q_ttr=1600)
    r1 = _fake_lineup_result("qttr_max", 3100, 1550.0, 100, [p1, p2])
    s1 = ScenarioResult.from_lineup(1, size=2, result=r1)
    row1 = s1.to_row(best_total=3100)
    # Second to last column now holds BestDelta; last column is Scenario label (optional)
    assert row1[-2] == "0"  # delta vs best is zero
    assert row1[-1] == ""  # scenario label empty
    # worse scenario
    r2 = _fake_lineup_result("qttr_max", 3000, 1500.0, 200, [p1, p2])
    s2 = ScenarioResult.from_lineup(2, size=2, result=r2)
    row2 = s2.to_row(best_total=3100)
    assert row2[-2] == "-100"  # 3000 - 3100
