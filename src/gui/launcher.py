"""GUI launch utilities."""

from __future__ import annotations

import os
from typing import Optional

from PyQt6.QtWidgets import QApplication

from config.app_settings import load_settings
from .theme import apply_theme
from .main_window import MainWindow
from .splash import create_splash


def run_gui(enable_splash: bool = True) -> int:
    # Support repeated test runs by reusing existing app instance.
    app = QApplication.instance() or QApplication([])

    # Offscreen support for CI/testing if set externally
    if os.environ.get("QT_QPA_PLATFORM") == "offscreen":
        enable_splash = False

    settings = load_settings()
    apply_theme(app, settings.theme if settings.theme in {"light", "dark"} else "light")

    splash = create_splash() if enable_splash else None
    window = MainWindow()
    window.show()
    if splash:
        splash.finish(window)
    return app.exec()


__all__ = ["run_gui"]
