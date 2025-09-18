"""Convenience launcher to run the GUI without needing package install.

Usage:
  python run_gui.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from config.logging_config import configure_logging  # type: ignore  # noqa: E402
from config.app_settings import load_settings  # type: ignore  # noqa: E402
from gui.launcher import run_gui  # type: ignore  # noqa: E402


def main() -> int:
    configure_logging()
    return run_gui()


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
