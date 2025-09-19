from __future__ import annotations

"""Lightweight smoke tests ensuring GUI modules import without side effects.

These tests help catch syntax errors or misplaced top-level code (e.g.,
indentation mistakes that reference `self` outside a class) early.

They run in offscreen mode so that a display server isn't required.
"""

import os
import pytest

try:  # Determine if PyQt6 is available; if not, skip these tests.
    import PyQt6  # type: ignore  # noqa: F401
    HAS_PYQT = True
except Exception:  # pragma: no cover
    HAS_PYQT = False

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.mark.parametrize(
    "module_name",
    [
        "gui.launcher",
        "gui.main_window",
        "gui.matches_tab",
        "gui.optimization_tab",
    ],
)
def test_gui_module_import(module_name: str):
    if not HAS_PYQT:
        pytest.skip("PyQt6 not installed; skipping GUI import smoke test.")
    __import__(module_name)
