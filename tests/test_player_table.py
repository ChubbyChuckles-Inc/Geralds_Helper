from __future__ import annotations

import os
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PyQt6.QtWidgets import QApplication  # type: ignore

    _PYQT_AVAILABLE = True
except Exception:  # pragma: no cover
    _PYQT_AVAILABLE = False

from data.player import Player


def _app():  # helper ensures single instance
    if not _PYQT_AVAILABLE:
        pytest.skip("PyQt6 not available")
    return QApplication.instance() or QApplication([])


def test_player_table_add_and_filter() -> None:
    _app()
    if not _PYQT_AVAILABLE:
        pytest.skip("PyQt6 not available")
    from gui.player_table import PlayerTable  # type: ignore

    table = PlayerTable([])
    table.add_player(Player(name="Alice", q_ttr=1500, team="Alpha"))
    table.add_player(Player(name="Bob", q_ttr=1400, team="Beta"))
    assert table.rowCount() == 2
    table.filter("ali")
    # Count visible rows
    visible = sum(0 if table.isRowHidden(r) else 1 for r in range(table.rowCount()))
    assert visible == 1
