"""HTTP fetching utilities with polite defaults.

All network access is centralized here to allow unit tests to monkeypatch
`Fetcher.get` or provide a FakeFetcher that returns stored HTML.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Optional, Callable
import time
import requests
import os
import hashlib
import json
from pathlib import Path


DEFAULT_UA = (
    "GeraldsHelperScraper/0.1 (+https://example.invalid; respectful; contact owner if issues)"
)


class SupportsGet(Protocol):  # pragma: no cover - structural typing
    def get(self, url: str, *, timeout: float | None = None) -> str: ...


@dataclass
class Fetcher:
    """Simple fetcher with retry + backoff."""

    user_agent: str = DEFAULT_UA
    retries: int = 2
    backoff: float = 0.75
    timeout: float = 10.0
    throttle: float = 0.0  # seconds to sleep after each request

    def get(self, url: str, *, timeout: float | None = None) -> str:
        last_exc: Optional[Exception] = None
        for attempt in range(self.retries + 1):
            try:
                resp = requests.get(
                    url,
                    headers={
                        "User-Agent": self.user_agent,
                        "Accept": "text/html,application/xhtml+xml",
                    },
                    timeout=timeout or self.timeout,
                    allow_redirects=True,
                )
                if os.environ.get("DEBUG_SCRAPE"):
                    chain = (
                        " -> ".join(r.url for r in resp.history)
                        + (" -> " if resp.history else "")
                        + resp.url
                    )
                    print(
                        f"[debug][fetch] GET {url} status={resp.status_code} chain={chain} len={len(resp.text)}"
                    )
                resp.raise_for_status()
                if self.throttle > 0:
                    time.sleep(self.throttle)
                # site likely declares ISO-8859-1; requests guesses correctly; ensure text returned.
                return resp.text
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                if attempt < self.retries:
                    time.sleep(self.backoff * (attempt + 1))
        assert last_exc is not None
        raise last_exc


class FakeFetcher:
    """Fetcher backed by an in-memory mapping for tests."""

    def __init__(self, mapping: dict[str, str]):
        self._mapping = mapping

    def get(self, url: str, *, timeout: float | None = None) -> str:  # noqa: D401
        try:
            return self._mapping[url]
        except KeyError as e:  # pragma: no cover - explicit failure path
            raise RuntimeError(f"No fixture for URL: {url}") from e


__all__ = ["Fetcher", "FakeFetcher", "SupportsGet"]


class CachedFetcher(Fetcher):
    """Fetcher with optional on-disk + in-memory caching.

    Cache key = SHA1(url). Stored as JSON with fields {"url":..., "text":..., "ts": epoch}.
    TTL applies only for disk reload; if expired we refetch and overwrite.
    """

    def __init__(
        self,
        cache_dir: str | Path = ".cache_scrape",
        ttl_seconds: int = 3600,
        enable_memory: bool = True,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.cache_dir = Path(cache_dir)
        self.ttl = ttl_seconds
        self.enable_memory = enable_memory
        self._mem: dict[str, tuple[float, str]] = {}
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get(self, url: str, *, timeout: float | None = None) -> str:  # type: ignore[override]
        now = time.time()
        key = hashlib.sha1(url.encode("utf-8")).hexdigest()
        # Memory cache
        if self.enable_memory:
            hit = self._mem.get(key)
            if hit and (now - hit[0]) < self.ttl:
                return hit[1]
        path = self.cache_dir / f"{key}.json"
        if path.exists():
            try:
                obj = json.loads(path.read_text(encoding="utf-8"))
                if (now - float(obj.get("ts", 0))) < self.ttl:
                    text = obj["text"]
                    if self.enable_memory:
                        self._mem[key] = (now, text)
                    return text
            except Exception:
                pass
        text = super().get(url, timeout=timeout)
        try:
            path.write_text(json.dumps({"url": url, "text": text, "ts": now}), encoding="utf-8")
            if self.enable_memory:
                self._mem[key] = (now, text)
        except Exception:
            pass
        return text


__all__.append("CachedFetcher")


class SessionFetcher(Fetcher):
    """Stateful fetcher that keeps a requests.Session and performs an initial handshake.

    Some sites deliver full content only after a landing page establishes cookies.
    We mimic a lightweight browser sequence (landing on root, then Ergebnisse page)
    before requesting the target URL. DEBUG_SCRAPE logs handshake steps.
    """

    def __init__(self, *args, handshake: bool = True, **kwargs):
        super().__init__(*args, **kwargs)
        self._sess = requests.Session()
        self.handshake_done = False
        self.do_handshake = handshake

    def _maybe_handshake(self, base_url: str):
        if self.handshake_done or not self.do_handshake:
            return
        import os

        steps = [
            base_url,
            base_url.rstrip("/") + "/Default.aspx?Page=Start",
            base_url.rstrip("/") + "/Default.aspx?Page=Ergebnisse",
        ]
        for s in steps:
            try:
                r = self._sess.get(
                    s,
                    headers={
                        "User-Agent": self.user_agent,
                        "Accept": "text/html,application/xhtml+xml",
                        "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
                        "Connection": "keep-alive",
                    },
                    timeout=self.timeout,
                    allow_redirects=True,
                )
                if os.environ.get("DEBUG_SCRAPE"):
                    chain = (
                        " -> ".join(h.url for h in r.history)
                        + (" -> " if r.history else "")
                        + r.url
                    )
                    print(
                        f"[debug][handshake] {s} status={r.status_code} chain={chain} len={len(r.text)}"
                    )
            except Exception as e:  # pragma: no cover
                if os.environ.get("DEBUG_SCRAPE"):
                    print(f"[debug][handshake] failed {s}: {e}")
        self.handshake_done = True

    def get(self, url: str, *, timeout: float | None = None) -> str:  # type: ignore[override]
        from urllib.parse import urlparse

        parsed = urlparse(url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        self._maybe_handshake(base)
        import os, time

        last_exc: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                r = self._sess.get(
                    url,
                    headers={
                        "User-Agent": self.user_agent,
                        "Accept": "text/html,application/xhtml+xml",
                        "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
                        "Connection": "keep-alive",
                        "Referer": base + "/Default.aspx?Page=Ergebnisse",
                    },
                    timeout=timeout or self.timeout,
                    allow_redirects=True,
                )
                r.raise_for_status()
                if os.environ.get("DEBUG_SCRAPE"):
                    chain = (
                        " -> ".join(h.url for h in r.history)
                        + (" -> " if r.history else "")
                        + r.url
                    )
                    print(
                        f"[debug][session_fetch] {url} status={r.status_code} chain={chain} len={len(r.text)})"
                    )
                if self.throttle:
                    time.sleep(self.throttle)
                return r.text
            except Exception as e:  # noqa: BLE001
                last_exc = e
                if attempt < self.retries:
                    time.sleep(self.backoff * (attempt + 1))
        assert last_exc is not None
        raise last_exc


__all__.append("SessionFetcher")
