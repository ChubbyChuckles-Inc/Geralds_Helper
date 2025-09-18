"""GUI launch utilities."""

from __future__ import annotations

import os
from typing import Optional

try:  # Defensive import with clearer diagnostics
    from PyQt6.QtWidgets import QApplication
except Exception as exc:  # pragma: no cover - import failure diagnostics
    raise RuntimeError(
        "Failed to import PyQt6.QtWidgets. Ensure PyQt6 is installed and that Qt platform plugins are available."
    ) from exc

from config.app_settings import load_settings
from .theme import apply_theme
from .main_window import MainWindow
from .splash import create_splash


def run_gui(enable_splash: bool = True) -> int:
    # Support repeated test runs by reusing existing app instance.
    try:
        app = QApplication.instance() or QApplication([])
    except Exception as exc:  # pragma: no cover - runtime init failure
        raise RuntimeError(
            "Failed to initialize QApplication. If this is a Windows environment, verify that the 'platforms' plugins directory is present (e.g., PyQt6/Qt6/plugins/platforms) and that your PATH or QT_QPA_PLATFORM_PLUGIN_PATH is set appropriately."
        ) from exc

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
