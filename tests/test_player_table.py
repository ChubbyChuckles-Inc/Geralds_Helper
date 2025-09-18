from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from data.player import Player
from gui.player_table import PlayerTable


def _app() -> QApplication:  # helper ensures single instance
    return QApplication.instance() or QApplication([])


def test_player_table_add_and_filter() -> None:
    app = _app()
    table = PlayerTable([])
    table.add_player(Player(name="Alice", q_ttr=1500, team="Alpha"))
    table.add_player(Player(name="Bob", q_ttr=1400, team="Beta"))
    assert table.rowCount() == 2
    table.filter("ali")
    # Count visible rows
    visible = sum(0 if table.isRowHidden(r) else 1 for r in range(table.rowCount()))
    assert visible == 1
