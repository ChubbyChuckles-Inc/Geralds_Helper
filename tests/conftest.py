"""Pytest fixtures for the project."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Iterator

import pytest

# Ensure src/ is on path for direct module imports when running tests
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from config.app_settings import CONFIG_FILE, DEFAULT_CONFIG  # type: ignore  # noqa: E402


@pytest.fixture(autouse=True)
def _isolate_config(tmp_path: Path) -> Iterator[None]:
    """Isolate configuration file per test to avoid cross-test pollution."""
    original = CONFIG_FILE
    backup = None
    if original.exists():
        backup = original.read_text(encoding="utf-8")
    try:
        if original.exists():
            original.unlink()
        # Write default config for each test
        original.write_text(json.dumps(DEFAULT_CONFIG), encoding="utf-8")
        yield
    finally:
        if backup is not None:
            original.write_text(backup, encoding="utf-8")
        else:
            if original.exists():
                original.unlink()
