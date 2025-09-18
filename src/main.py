"""Application entry point.

Currently provides a placeholder CLI startup. GUI bootstrap will be added in the
"GUI Development - Core Framework" phase. This keeps early setup lightweight
while allowing logging + configuration to be validated.
"""

from __future__ import annotations

import logging
import argparse

from config.logging_config import configure_logging
from config.app_settings import load_settings

try:  # Optional import so non-GUI environments still function
    from gui.launcher import run_gui  # type: ignore
except Exception:  # pragma: no cover
    run_gui = None  # type: ignore


def main(argv: list[str] | None = None) -> int:
    """Run the application entry logic.

    Returns
    -------
    int
        Process exit code (0 for success).
    """
    parser = argparse.ArgumentParser(description="Table Tennis Team Manager")
    parser.add_argument("--gui", action="store_true", help="Launch the graphical interface")
    args = parser.parse_args(argv)

    configure_logging()
    log = logging.getLogger(__name__)
    settings = load_settings()
    log.info(
        "Launching Table Tennis Team Manager (theme=%s, window=%sx%s)",
        settings.theme,
        settings.window_width,
        settings.window_height,
    )
    if args.gui and run_gui:
        print("Launching GUI…")
        return run_gui()
    print("Table Tennis Team Manager bootstrap successful.")
    return 0  # CLI mode


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
