from __future__ import annotations

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from gui.main_window import MainWindow
from gui.theme import apply_theme


@pytest.fixture(scope="module")
def app() -> QApplication:  # type: ignore
    return QApplication.instance() or QApplication([])


def test_main_window_tabs(app: QApplication) -> None:
    w = MainWindow()
    names = w.tab_names()
    assert {"Players", "Matches", "Optimization"}.issubset(set(names))


def test_theme_switch(app: QApplication) -> None:
    w = MainWindow()
    apply_theme(app, "dark")
    dark_style = app.styleSheet()
    apply_theme(app, "light")
    light_style = app.styleSheet()
    assert dark_style != light_style and len(dark_style) > 10 and len(light_style) > 10
