from data.player import Player
from optimization.what_if import run_what_if_scenarios
from optimization.optimizer import optimize_lineup
from optimization.scenario import ScenarioResult


def _players():
    return [
        Player(name="Alice", q_ttr=1500),
        Player(name="Bob", q_ttr=1600),
        Player(name="Cara", q_ttr=1550),
        Player(name="Dan", q_ttr=1400),
    ]


def test_run_what_if_basic():
    players = _players()
    scenarios = [
        {"name": "Base", "exclude_names": []},
        {"name": "No Bob", "exclude_names": ["Bob"]},
        {"name": "No Top", "exclude_names": ["Bob", "Cara"]},
    ]
    results = run_what_if_scenarios(players, scenarios, size=2, objective="qttr_max")
    assert len(results) == 3
    # Base should include Bob (highest) + Cara
    base = results[0]
    assert base.scenario_name == "Base"
    names0 = {p["name"] for p in base.players}
    assert {"Bob", "Cara"} == names0
    nobob = results[1]
    names1 = {p["name"] for p in nobob.players}
    assert "Bob" not in names1
    notop = results[2]
    # If excluding Bob and Cara, next best pair should include Alice
    names2 = {p["name"] for p in notop.players}
    assert "Alice" in names2 or notop.players == []  # allow empty if insufficient


def test_scenario_result_row_has_name():
    players = _players()
    res = optimize_lineup(players, size=2, objective="qttr_max")
    sr = ScenarioResult.from_lineup(1, size=2, result=res)
    sr.scenario_name = "Base"
    row = sr.to_row(best_total=sr.total_qttr)
    # Expect 9 columns including Scenario
    assert len(row) == 9
    assert row[-1] == "Base"
