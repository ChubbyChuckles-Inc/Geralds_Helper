"""Threaded workers for scraping operations.

Provides QThread-compatible worker objects (QObject with run method) emitting
progress, error, and finished signals so the GUI stays responsive.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional
import traceback
import logging

from PyQt6.QtCore import QObject, pyqtSignal
import time

from scraping.adapter import get_club_teams, get_team_players, get_division_schedule
from scraping.models import ClubTeam
from data.player import Player
from data.match import Match

log = logging.getLogger(__name__)


class FetchTeamsWorker(QObject):  # pragma: no cover - thread behavior
    progress = pyqtSignal(str)
    error = pyqtSignal(str)
    finished = pyqtSignal(object)

    def __init__(self, club_url: str, club_html_path: Optional[Path], retries: int = 2):
        super().__init__()
        self._club_url = club_url
        self._club_html_path = club_html_path
        self._cancelled = False
        self._retries = retries

    def cancel(self):  # pragma: no cover
        self._cancelled = True

    def run(self) -> None:  # executed in thread
        attempt = 0
        while attempt <= self._retries and not self._cancelled:
            try:
                self.progress.emit(f"Fetching club teams… (attempt {attempt+1}/{self._retries+1})")
                teams = get_club_teams(self._club_url, club_html_path=self._club_html_path)
                for t in teams:
                    t.derive_ids()
                if self._cancelled:
                    break
                self.progress.emit(f"Parsed {len(teams)} teams")
                self.finished.emit({"teams": teams, "cancelled": self._cancelled})
                return
            except Exception as exc:  # noqa: BLE001
                log.warning("FetchTeamsWorker attempt %d failed: %s", attempt + 1, exc)
                if attempt == self._retries:
                    self.error.emit(str(exc))
                    self.finished.emit({"teams": [], "cancelled": self._cancelled})
                    return
                backoff = 1.5**attempt
                self.progress.emit(f"Retrying in {backoff:.1f}s…")
                time.sleep(backoff)
                attempt += 1


class LoadRosterWorker(QObject):  # pragma: no cover - thread behavior
    progress = pyqtSignal(str)
    error = pyqtSignal(str)
    finished = pyqtSignal(object)

    def __init__(
        self,
        base_url: str,
        team: ClubTeam,
        team_html_path: Optional[Path],
        import_schedule: bool,
        division_html_path: Optional[Path] = None,
        retries: int = 1,
    ):
        super().__init__()
        self._base_url = base_url
        self._team = team
        self._team_html_path = team_html_path
        self._import_schedule = import_schedule
        self._division_html_path = division_html_path
        self._retries = retries
        self._cancelled = False

    def cancel(self):  # pragma: no cover
        self._cancelled = True

    def run(self) -> None:  # executed in thread
        players: List[Player] = []
        matches: List[Match] = []
        attempt = 0
        while attempt <= self._retries and not self._cancelled:
            try:
                self.progress.emit(
                    f"Loading roster for {self._team.name}… (attempt {attempt+1}/{self._retries+1})"
                )
                players = get_team_players(
                    self._base_url, self._team, team_html_path=self._team_html_path
                )
                if self._cancelled:
                    break
                self.progress.emit(f"Loaded {len(players)} players")
                if self._import_schedule and not self._cancelled:
                    try:
                        self.progress.emit("Importing schedule…")
                        matches = get_division_schedule(
                            self._base_url,
                            self._team,
                            division_html_path=self._division_html_path,
                        )
                        self.progress.emit(f"Imported {len(matches)} matches")
                    except Exception as exc:  # noqa: BLE001
                        log.warning("Schedule import failed: %s", exc)
                        self.progress.emit(f"Schedule import failed: {exc}")
                self.finished.emit(
                    {
                        "players": players,
                        "matches": matches,
                        "cancelled": self._cancelled,
                    }
                )
                return
            except Exception as exc:  # noqa: BLE001
                log.warning("LoadRosterWorker attempt %d failed: %s", attempt + 1, exc)
                if attempt == self._retries:
                    self.error.emit(str(exc))
                    self.finished.emit(
                        {"players": players, "matches": matches, "cancelled": self._cancelled}
                    )
                    return
                backoff = 1.8**attempt
                self.progress.emit(f"Retrying in {backoff:.1f}s…")
                time.sleep(backoff)
                attempt += 1


__all__ = ["FetchTeamsWorker", "LoadRosterWorker"]
