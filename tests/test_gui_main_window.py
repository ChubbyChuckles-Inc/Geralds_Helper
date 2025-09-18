from __future__ import annotations

import os
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PyQt6.QtWidgets import QApplication  # type: ignore
    from gui.main_window import MainWindow  # type: ignore
    from gui.theme import apply_theme  # type: ignore

    _PYQT_AVAILABLE = True
except Exception:  # pragma: no cover
    _PYQT_AVAILABLE = False


@pytest.fixture(scope="module")
def app():  # type: ignore
    if not _PYQT_AVAILABLE:
        pytest.skip("PyQt6 not available")
    return QApplication.instance() or QApplication([])


def test_main_window_tabs(app):  # type: ignore
    if not _PYQT_AVAILABLE:
        pytest.skip("PyQt6 not available")
    w = MainWindow()
    names = w.tab_names()
    assert {"Players", "Matches", "Optimization"}.issubset(set(names))


def test_theme_switch(app):  # type: ignore
    if not _PYQT_AVAILABLE:
        pytest.skip("PyQt6 not available")
    w = MainWindow()
    apply_theme(app, "dark")
    dark_style = app.styleSheet()
    apply_theme(app, "light")
    light_style = app.styleSheet()
    assert dark_style != light_style and len(dark_style) > 10 and len(light_style) > 10
