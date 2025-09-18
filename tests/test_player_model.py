from __future__ import annotations

from data.player import Player


def test_player_history_and_serialization() -> None:
    p = Player(name="Alice", q_ttr=1500, team="A")
    p.add_history_point(1510)
    d = p.to_dict()
    clone = Player.from_dict(d)
    assert clone.name == "Alice"
    assert clone.q_ttr == 1510
    assert len(clone.history) == 1
