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

# Ensure PyQt6 import works even if user launched with system Python instead of venv
try:  # noqa: SIM105
    import PyQt6  # type: ignore  # noqa: F401
except Exception:  # pragma: no cover - fallback path
    venv_site = ROOT / ".venv" / "Lib" / "site-packages"
    if venv_site.exists() and str(venv_site) not in sys.path:
        sys.path.insert(0, str(venv_site))
        try:
            import PyQt6  # type: ignore  # noqa: F401
        except Exception as exc:  # pragma: no cover
            print(
                "Failed to import PyQt6 even after adding .venv site-packages. Install dependencies with 'pip install -r requirements.txt'.",
                file=sys.stderr,
            )
            raise

from gui.launcher import run_gui  # type: ignore  # noqa: E402


def main() -> int:
    configure_logging()
    return run_gui()


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
