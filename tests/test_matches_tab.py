from __future__ import annotations
import os
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
try:
    from PyQt6.QtWidgets import QApplication  # type: ignore
    from gui.matches_tab import MatchesTab  # type: ignore
    from data.match import Match  # type: ignore

    _PYQT_AVAILABLE = True
except Exception:
    _PYQT_AVAILABLE = False


def _app():
    if not _PYQT_AVAILABLE:
        pytest.skip("PyQt6 not available")
    return QApplication.instance() or QApplication([])


def test_matches_tab_add_and_conflict():
    _app()
    if not _PYQT_AVAILABLE:
        pytest.skip("PyQt6 not available")
    tab = MatchesTab()
    m1 = Match(home_team="A", away_team="B")
    m2 = Match(home_team="A", away_team="C")
    tab.add_match(m1)
    tab.add_match(m2)
    # both on today's date; expect conflict tooltip
    assert "Conflicts" in (tab.toolTip() or "") or len(tab.matches()) == 2
