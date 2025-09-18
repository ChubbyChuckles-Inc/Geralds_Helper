"""Logging configuration utilities.

Sets up a rotating file handler and console logging with structured, concise formatting.
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "app.log"


def configure_logging(
    level: int = logging.INFO, max_bytes: int = 512_000, backups: int = 3
) -> None:
    """Configure application-wide logging.

    Parameters
    ----------
    level: int
        Root logger level.
    max_bytes: int
        Max size of each rotating log file.
    backups: int
        Number of backup log files to retain.
    """
    if getattr(configure_logging, "_configured", False):  # idempotent
        return

    fmt = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)

    root = logging.getLogger()
    root.setLevel(level)

    # Console handler
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    root.addHandler(ch)

    # Rotating file handler
    fh = RotatingFileHandler(LOG_FILE, maxBytes=max_bytes, backupCount=backups, encoding="utf-8")
    fh.setFormatter(formatter)
    root.addHandler(fh)

    configure_logging._configured = True  # type: ignore[attr-defined]


__all__ = ["configure_logging", "LOG_FILE"]
