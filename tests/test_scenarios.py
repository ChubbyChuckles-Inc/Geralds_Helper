from optimization.scenario import ScenarioResult, export_markdown
from optimization.optimizer import optimize_lineup
from data.player import Player


def test_export_markdown_basic():
    players = [
        Player(name="A", q_ttr=1000),
        Player(name="B", q_ttr=1100),
        Player(name="C", q_ttr=900),
    ]
    res = optimize_lineup(players, size=2, objective="qttr_max")
    s = ScenarioResult.from_lineup(1, size=2, result=res)
    md = export_markdown([s])
    assert "Optimization Scenarios Report" in md
    assert "| 1 |" in md
    assert "A" in md or "B" in md  # lineup names appear


def test_availability_filtering_integration():
    # Simulate availability filtering by invoking optimize_lineup directly on filtered players
    p1 = Player(name="A", q_ttr=1000)
    p2 = Player(name="B", q_ttr=1200)
    p3 = Player(name="C", q_ttr=800)
    # Only p2 available on given date
    date_iso = "2030-01-15"
    p2.availability.add(date_iso)
    # Filtering logic from OptimizationTab would keep players with empty availability (treated universal) OR date present
    pool = []
    for p in [p1, p2, p3]:
        if not p.availability or date_iso in p.availability:
            pool.append(p)
    # All players except those with restrictive availability not matching date should remain; p1 and p3 empty sets => included, p2 included (matches)
    res = optimize_lineup(pool, size=2, objective="qttr_max")
    # Highest two ratings among included pool are 1200 and 1000
    ratings = sorted(p.q_ttr for p in res.players)
    assert ratings == [1000, 1200]
