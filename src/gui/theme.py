"""Theme management utilities for applying light/dark styles."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from PyQt6.QtWidgets import QApplication

THEME_TYPE = Literal["light", "dark", "system"]

STYLES_DIR = Path("resources/styles")


def _read_style(name: str) -> str:
    path = STYLES_DIR / f"{name}.qss"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


LIGHT_STYLE = _read_style("light")
DARK_STYLE = _read_style("dark")


def apply_theme(app: QApplication, theme: THEME_TYPE) -> None:
    """Apply a theme to the QApplication.

    'system' currently defaults to light until OS integration is added.
    """
    if theme == "dark":
        app.setStyleSheet(DARK_STYLE)
    elif theme == "light" or theme == "system":
        app.setStyleSheet(LIGHT_STYLE)


__all__ = ["apply_theme", "THEME_TYPE"]
