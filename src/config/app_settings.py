"""Application settings loading and management."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict

DEFAULT_CONFIG = {
    "theme": "system",  # dark | light | system
    "window": {"width": 1200, "height": 800},
    "scraping": {"rate_limit_seconds": 2.0, "cache_ttl_minutes": 60},
}

CONFIG_DIR = Path("config")
CONFIG_DIR.mkdir(exist_ok=True)
CONFIG_FILE = CONFIG_DIR / "app_settings.json"


def _write_default_if_missing() -> None:
    if not CONFIG_FILE.exists():
        CONFIG_FILE.write_text(json.dumps(DEFAULT_CONFIG, indent=2), encoding="utf-8")


@dataclass
class AppSettings:
    raw: Dict[str, Any] = field(default_factory=lambda: DEFAULT_CONFIG.copy())

    @property
    def theme(self) -> str:
        return str(self.raw.get("theme", "system"))

    @property
    def window_width(self) -> int:
        return int(self.raw.get("window", {}).get("width", 1200))

    @property
    def window_height(self) -> int:
        return int(self.raw.get("window", {}).get("height", 800))

    @property
    def rate_limit_seconds(self) -> float:
        return float(self.raw.get("scraping", {}).get("rate_limit_seconds", 2.0))

    @property
    def cache_ttl_minutes(self) -> int:
        return int(self.raw.get("scraping", {}).get("cache_ttl_minutes", 60))


def load_settings() -> AppSettings:
    _write_default_if_missing()
    try:
        data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except Exception:
        data = DEFAULT_CONFIG.copy()
    return AppSettings(raw=data)


__all__ = ["AppSettings", "load_settings", "CONFIG_FILE"]
