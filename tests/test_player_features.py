from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

try:
    from PyQt6.QtWidgets import QApplication  # type: ignore

    _PYQT_AVAILABLE = True
except Exception:  # pragma: no cover - environment without PyQt6
    _PYQT_AVAILABLE = False

from data.player import Player
from data.serialization import save_players_json, load_players_json


def _app():  # helper
    if not _PYQT_AVAILABLE:
        pytest.skip("PyQt6 not available")
    return QApplication.instance() or QApplication([])


def test_player_availability_and_serialization(tmp_path):
    p = Player(name="Test", q_ttr=1000)
    p.toggle_availability("2025-01-01")
    p.add_history_point(1010)
    out = tmp_path / "players.json"
    save_players_json([p], out)
    loaded = load_players_json(out)[0]
    assert "2025-01-01" in loaded.availability
    assert loaded.q_ttr == 1010
    assert loaded.history


def test_bulk_set_team():
    if not _PYQT_AVAILABLE:
        pytest.skip("PyQt6 not available")
    # Import inside test to avoid import error during collection
    from gui.player_table import PlayerTable  # type: ignore

    _app()
    table = PlayerTable([])
    table.add_player(Player(name="A", q_ttr=1))
    table.add_player(Player(name="B", q_ttr=2))
    table.selectRow(0)
    table.selectRow(1)
    table.bulk_set_team("X")
    teams = {p.team for p in table.players()}
    assert teams == {"X"}
