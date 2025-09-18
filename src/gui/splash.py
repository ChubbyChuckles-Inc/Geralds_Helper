"""Splash screen support."""

from __future__ import annotations

from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QSplashScreen


def create_splash(message: str = "Loading…") -> QSplashScreen:
    # Placeholder blank pixmap; replace with logo later.
    pixmap = QPixmap(400, 240)
    pixmap.fill()  # default fill
    splash = QSplashScreen(pixmap)
    splash.showMessage(message)
    return splash


__all__ = ["create_splash"]
