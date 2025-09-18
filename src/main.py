"""Application entry point.

Currently provides a placeholder CLI startup. GUI bootstrap will be added in the
"GUI Development - Core Framework" phase. This keeps early setup lightweight
while allowing logging + configuration to be validated.
"""

from __future__ import annotations

import logging
from pathlib import Path

from config.logging_config import configure_logging
from config.app_settings import load_settings


def main() -> int:
    """Run the application entry logic.

    Returns
    -------
    int
        Process exit code (0 for success).
    """
    configure_logging()
    log = logging.getLogger(__name__)
    settings = load_settings()
    log.info(
        "Launching Table Tennis Team Manager (theme=%s, window=%sx%s)",
        settings.theme,
        settings.window_width,
        settings.window_height,
    )
    # Placeholder until GUI implemented
    print("Table Tennis Team Manager bootstrap successful.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
