"""Headless browser fetcher for dynamic pages.

Uses Playwright (synchronous API) to load a page, wait for a marker that
indicates the dynamic team overview content has appeared, then returns the
final HTML. We keep this isolated so the rest of the scraping stack can
remain unchanged; just swap in this fetcher.

Installation (one-time after adding dependency):
  pip install playwright
  playwright install chromium

Environment variable HEADLESS_BROWSER=1 can be used to force this fetcher
in higher-level orchestration if desired.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol
import time


class SupportsGet(Protocol):  # pragma: no cover
    def get(self, url: str, *, timeout: float | None = None) -> str: ...


_PLAYWRIGHT_IMPORT_ERROR = (
    "Playwright is not installed. Install with 'pip install playwright' and then "
    "run 'playwright install chromium'."
)


@dataclass
class HeadlessFetcher:
    """Fetch dynamic HTML using Playwright Chromium in headless mode.

    Strategy:
      1. Load the target URL.
      2. If marker keywords absent, attempt fallback navigations:
         - Visit TTLV and Ergebnisse overview pages
         - Return to original URL
      3. Poll for marker keywords between navigations.
    """

    timeout: float = 30.0  # seconds overall
    wait_selector: str = "body"
    extra_wait_for_keywords: tuple[str, ...] = ("Zum Team", "Mannschaft", "Wettbewerb")
    throttle: float = 0.0
    user_agent: str | None = None
    navigation_retry_delay: float = 0.6

    def __post_init__(self) -> None:  # lazy; nothing to init yet
        pass

    def _debug(self, msg: str) -> None:
        import os

        if os.environ.get("DEBUG_SCRAPE"):
            print(f"[debug][headless] {msg}")

    def _poll_for_keywords(self, page, deadline: float) -> str:
        # Poll page content for keywords until deadline
        last_html = ""
        import time as _t

        while _t.time() < deadline:
            html = page.content()
            if any(k in html for k in self.extra_wait_for_keywords):
                return html
            last_html = html
            _t.sleep(0.5)
        return last_html

    def get(self, url: str, *, timeout: float | None = None) -> str:  # noqa: D401
        to = timeout or self.timeout
        try:
            from playwright.sync_api import sync_playwright  # type: ignore
        except Exception as e:  # pragma: no cover - environment issue
            raise RuntimeError(_PLAYWRIGHT_IMPORT_ERROR) from e
        start = time.time()
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = (
                browser.new_context(user_agent=self.user_agent)
                if self.user_agent
                else browser.new_context()
            )
            page = context.new_page()
            page.set_default_timeout(int(to * 1000))
            self._debug(f"goto initial {url}")
            page.goto(url, wait_until="domcontentloaded")
            try:
                page.wait_for_selector(self.wait_selector, timeout=int(to * 1000 / 3))
            except Exception:
                self._debug("base selector wait timed out")
            deadline = start + to
            html = self._poll_for_keywords(page, deadline)
            if any(k in html for k in self.extra_wait_for_keywords):
                self._debug("keywords found after initial load")
                result = html
            else:
                result = html
                # Attempt fallback navigations
                # 1. Try TTLV page then back
                from urllib.parse import urlparse

                parsed = urlparse(url)
                base = f"{parsed.scheme}://{parsed.netloc}"
                ttlv_url = base + "/Default.aspx?Page=TTLV"
                erg_url = base + "/Default.aspx?Page=Ergebnisse"
                for nav_url in (ttlv_url, erg_url, url):
                    if time.time() > deadline:
                        break
                    self._debug(f"goto fallback {nav_url}")
                    try:
                        page.goto(nav_url, wait_until="domcontentloaded")
                    except Exception as e:  # noqa: BLE001
                        self._debug(f"navigation error {e}")
                        continue
                    time.sleep(self.navigation_retry_delay)
                    html = self._poll_for_keywords(page, deadline)
                    if any(k in html for k in self.extra_wait_for_keywords):
                        self._debug(f"keywords found after fallback {nav_url}")
                        result = html
                        break
                else:
                    self._debug("no keywords found after fallbacks")
            browser.close()
            if self.throttle:
                time.sleep(self.throttle)
            return result


__all__ = ["HeadlessFetcher", "SupportsGet"]
