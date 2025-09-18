from __future__ import annotations

"""Lightweight smoke tests ensuring GUI modules import without side effects.

These tests help catch syntax errors or misplaced top-level code (e.g.,
indentation mistakes that reference `self` outside a class) early.

They run in offscreen mode so that a display server isn't required.
"""

import os
import pytest

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
    __import__(module_name)
