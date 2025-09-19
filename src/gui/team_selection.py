"""Dialog to select a club team and load its players via scraping."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional
import traceback
import logging

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QFileDialog,
    QMessageBox,
    QCheckBox,
)
from PyQt6.QtCore import Qt, QThread

from scraping.adapter import get_club_teams, get_team_players
from scraping.models import ClubTeam
from data.player import Player
from data.match import Match
from gui.workers import FetchTeamsWorker, LoadRosterWorker
from config.app_settings import CONFIG_FILE, load_settings

log = logging.getLogger(__name__)


class TeamSelectionDialog(QDialog):  # pragma: no cover - GUI interaction
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Load Club Team Roster")
        self._teams: List[ClubTeam] = []
        self._players: List[Player] = []
        self._matches: List[Match] = []
        self._threads: List[QThread] = []
        layout = QVBoxLayout(self)
        # Load settings for recent values
        try:
            self._app_settings = load_settings()
        except Exception:  # pragma: no cover - defensive
            self._app_settings = None

        # Base URL & optional offline HTML
        self._url_edit = QLineEdit()
        self._url_edit.setPlaceholderText("Full club page URL (with teams)")
        # Pre-fill last used URL if available
        if getattr(self, "_app_settings", None) and self._app_settings.last_club_url:
            self._url_edit.setText(self._app_settings.last_club_url)
        btn_browse_club = QPushButton("Club HTML…")
        btn_browse_team = QPushButton("Team HTML…")
        btn_browse_division = QPushButton("Division HTML…")
        btn_fetch = QPushButton("Fetch Teams")

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Club URL:"))
        row1.addWidget(self._url_edit)
        row1.addWidget(btn_browse_club)
        row1.addWidget(btn_browse_team)
        row1.addWidget(btn_browse_division)
        row1.addWidget(btn_fetch)
        layout.addLayout(row1)

        self._club_html_path: Optional[Path] = None
        self._team_html_path: Optional[Path] = None  # optional single-team override
        self._division_html_path: Optional[Path] = None  # optional division schedule snapshot

        # Teams list
        self._team_list = QListWidget()
        self._team_list.setSelectionMode(self._team_list.SelectionMode.SingleSelection)
        layout.addWidget(QLabel("Select Team:"))
        layout.addWidget(self._team_list)

        # Schedule import option
        self._import_schedule = QCheckBox("Import Schedule")
        self._import_schedule.setChecked(True)
        layout.addWidget(self._import_schedule)

        # Actions
        btn_load_roster = QPushButton("Load Roster")
        btn_cancel_task = QPushButton("Cancel Task")
        btn_cancel = QPushButton("Cancel")
        row2 = QHBoxLayout()
        row2.addStretch(1)
        row2.addWidget(btn_load_roster)
        row2.addWidget(btn_cancel_task)
        row2.addWidget(btn_cancel)
        layout.addLayout(row2)

        btn_fetch.clicked.connect(self._on_fetch)
        btn_browse_club.clicked.connect(self._on_browse_club_html)
        btn_browse_team.clicked.connect(self._on_browse_team_html)
        btn_browse_division.clicked.connect(self._on_browse_division_html)
        btn_load_roster.clicked.connect(self._on_load_roster)
        btn_cancel_task.clicked.connect(self._on_cancel_task)
        btn_cancel.clicked.connect(self.reject)

    def _on_browse_club_html(self):  # pragma: no cover
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Club Overview HTML", "", "HTML Files (*.html *.htm)"
        )
        if path:
            self._club_html_path = Path(path)

    def _on_browse_team_html(self):  # pragma: no cover
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Team Page HTML", "", "HTML Files (*.html *.htm)"
        )
        if path:
            self._team_html_path = Path(path)

    def _on_browse_division_html(self):  # pragma: no cover
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Division Spielplan HTML", "", "HTML Files (*.html *.htm)"
        )
        if path:
            self._division_html_path = Path(path)

    def _on_fetch(self):  # pragma: no cover
        url = self._url_edit.text().strip()
        if not url:
            QMessageBox.warning(self, "Input", "Please enter a club URL.")
            return
        self._set_enabled(False)
        self._fetch_worker = FetchTeamsWorker(url, self._club_html_path)
        worker = self._fetch_worker
        thread = QThread(self)
        worker.moveToThread(thread)
        worker.progress.connect(self._on_progress)
        worker.error.connect(self._on_error)
        worker.finished.connect(lambda payload: self._on_fetch_finished(payload, thread))
        thread.started.connect(worker.run)
        thread.start()
        self._threads.append(thread)

    def _on_fetch_finished(self, payload, thread: QThread):  # pragma: no cover
        teams = payload.get("teams", [])
        self._teams = teams
        self._team_list.clear()
        for t in teams:
            item = QListWidgetItem(t.name)
            item.setData(Qt.ItemDataRole.UserRole, t)
            self._team_list.addItem(item)
        if not teams:
            QMessageBox.information(self, "Teams", "No teams parsed.")
        self._set_enabled(True)
        thread.quit()
        thread.wait(200)

    def _on_progress(self, msg: str):  # pragma: no cover
        try:
            if self.parent() and hasattr(self.parent(), "statusBar"):
                self.parent().statusBar().showMessage(msg)
        except Exception:
            pass

    def _on_error(self, msg: str):  # pragma: no cover
        QMessageBox.warning(self, "Error", msg)

    def _on_load_roster(self):  # pragma: no cover
        items = self._team_list.selectedItems()
        if not items:
            QMessageBox.warning(self, "Roster", "Select a team first.")
            return
        team: ClubTeam = items[0].data(Qt.ItemDataRole.UserRole)
        base_url = self._url_edit.text().strip()
        self._set_enabled(False)
        self._roster_worker = LoadRosterWorker(
            base_url,
            team,
            self._team_html_path,
            self._import_schedule.isChecked(),
            division_html_path=self._division_html_path,
        )
        worker = self._roster_worker
        thread = QThread(self)
        worker.moveToThread(thread)
        worker.progress.connect(self._on_progress)
        worker.error.connect(self._on_error)
        worker.finished.connect(
            lambda payload: self._on_roster_finished(payload, team, base_url, thread)
        )
        thread.started.connect(worker.run)
        thread.start()
        self._threads.append(thread)

    def _on_roster_finished(
        self, payload, team: ClubTeam, base_url: str, thread: QThread
    ):  # pragma: no cover
        self._players = payload.get("players", [])
        self._matches = payload.get("matches", [])
        if not self._players:
            QMessageBox.information(self, "Roster", "No players parsed for team.")
        else:
            self._persist_recent(team, base_url)
            self.accept()
        self._set_enabled(True)
        thread.quit()
        thread.wait(200)

    def _persist_recent(self, team: ClubTeam, base_url: str):  # pragma: no cover
        try:
            import json

            data = (
                json.loads(CONFIG_FILE.read_text(encoding="utf-8")) if CONFIG_FILE.exists() else {}
            )
            data.setdefault("recent", {})
            data["recent"].update(
                {
                    "last_club_url": base_url,
                    "last_team_name": team.name,
                    "last_team_id": team.team_id,
                    "last_division_url": team.division_url,
                }
            )
            CONFIG_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception as exc:  # noqa: BLE001
            log.warning("Failed to persist recent settings: %s", exc)

    def _set_enabled(self, enabled: bool):  # pragma: no cover
        for w in [self._url_edit, self._team_list]:
            w.setEnabled(enabled)

    def _on_cancel_task(self):  # pragma: no cover
        # signal cancellation flags; threads will exit after current attempt
        try:
            if hasattr(self, "_fetch_worker") and self._fetch_worker:
                self._fetch_worker.cancel()
            if hasattr(self, "_roster_worker") and self._roster_worker:
                self._roster_worker.cancel()
            self._on_progress("Cancellation requested…")
        except Exception:
            pass

    def players(self) -> List[Player]:  # pragma: no cover
        return self._players

    def selected_team(self) -> Optional[ClubTeam]:  # pragma: no cover
        items = self._team_list.selectedItems()
        if not items:
            return None
        return items[0].data(Qt.ItemDataRole.UserRole)

    def matches(self) -> List["Match"]:  # pragma: no cover
        return self._matches


__all__ = ["TeamSelectionDialog"]
