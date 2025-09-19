from optimization.report import build_report
from optimization.scenario import ScenarioResult
from data.player import Player
from optimization.optimizer import LineupResult


class _LR(LineupResult):  # helper subclass to mimic LineupResult easily
    def __init__(self, players, total, avg, spread, objective):
        self.players = players
        self.total_qttr = total
        self.average_qttr = avg
        self.spread = spread
        self.objective = objective


def _mk_sr(idx: int, total: int, objective: str = "qttr_max"):
    p1 = Player(name=f"P{idx}A", q_ttr=total // 2)
    p2 = Player(name=f"P{idx}B", q_ttr=total - p1.q_ttr)
    lr = _LR(
        [p1, p2], total=total, avg=total / 2, spread=abs(p1.q_ttr - p2.q_ttr), objective=objective
    )
    sr = ScenarioResult.from_lineup(idx, size=2, result=lr)
    sr.scenario_name = f"Case {idx}"
    return sr


def test_build_report_empty():
    content = build_report([])
    assert "No scenarios" in content or "_No scenarios" in content


def test_build_report_content():
    history = [_mk_sr(1, 3100), _mk_sr(2, 3000), _mk_sr(3, 3200)]
    md = build_report(history)
    assert "Best Total" in md and "3200" in md
    assert "Totals Bar Chart" in md
    # Ensure scenario names appear
    assert "Case 1" in md and "Case 3" in md
