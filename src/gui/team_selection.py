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
)
from PyQt6.QtCore import Qt

from scraping.adapter import get_club_teams, get_team_players
from scraping.models import ClubTeam
from data.player import Player

log = logging.getLogger(__name__)


class TeamSelectionDialog(QDialog):  # pragma: no cover - GUI interaction
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Load Club Team Roster")
        self._teams: List[ClubTeam] = []
        self._players: List[Player] = []
        layout = QVBoxLayout(self)

        # Base URL & optional offline HTML
        self._url_edit = QLineEdit()
        self._url_edit.setPlaceholderText("Full club page URL (with teams)")
        btn_browse_club = QPushButton("Club HTML…")
        btn_fetch = QPushButton("Fetch Teams")

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Club URL:"))
        row1.addWidget(self._url_edit)
        row1.addWidget(btn_browse_club)
        row1.addWidget(btn_fetch)
        layout.addLayout(row1)

        self._club_html_path: Optional[Path] = None
        self._team_html_path: Optional[Path] = None  # optional single-team override

        # Teams list
        self._team_list = QListWidget()
        self._team_list.setSelectionMode(self._team_list.SelectionMode.SingleSelection)
        layout.addWidget(QLabel("Select Team:"))
        layout.addWidget(self._team_list)

        # Actions
        btn_load_roster = QPushButton("Load Roster")
        btn_cancel = QPushButton("Cancel")
        row2 = QHBoxLayout()
        row2.addStretch(1)
        row2.addWidget(btn_load_roster)
        row2.addWidget(btn_cancel)
        layout.addLayout(row2)

        btn_fetch.clicked.connect(self._on_fetch)
        btn_browse_club.clicked.connect(self._on_browse_club_html)
        btn_load_roster.clicked.connect(self._on_load_roster)
        btn_cancel.clicked.connect(self.reject)

    def _on_browse_club_html(self):  # pragma: no cover
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Club Overview HTML", "", "HTML Files (*.html *.htm)"
        )
        if path:
            self._club_html_path = Path(path)

    def _on_fetch(self):  # pragma: no cover
        url = self._url_edit.text().strip()
        if not url:
            QMessageBox.warning(self, "Input", "Please enter a club URL.")
            return
        try:
            teams = get_club_teams(url, club_html_path=self._club_html_path)
        except Exception as exc:  # noqa: BLE001
            log.error("Failed to fetch teams: %s", exc)
            traceback.print_exc()
            QMessageBox.warning(self, "Fetch Teams", f"Failed: {exc}")
            return
        self._teams = teams
        self._team_list.clear()
        for t in teams:
            item = QListWidgetItem(t.name)
            item.setData(Qt.ItemDataRole.UserRole, t)
            self._team_list.addItem(item)
        if not teams:
            QMessageBox.information(self, "Teams", "No teams parsed.")

    def _on_load_roster(self):  # pragma: no cover
        items = self._team_list.selectedItems()
        if not items:
            QMessageBox.warning(self, "Roster", "Select a team first.")
            return
        team: ClubTeam = items[0].data(Qt.ItemDataRole.UserRole)
        base_url = self._url_edit.text().strip()
        try:
            players = get_team_players(base_url, team, team_html_path=self._team_html_path)
        except Exception as exc:  # noqa: BLE001
            log.error("Failed to fetch players: %s", exc)
            traceback.print_exc()
            QMessageBox.warning(self, "Roster", f"Failed: {exc}")
            return
        if not players:
            QMessageBox.information(self, "Roster", "No players parsed for team.")
            return
        self._players = players
        self.accept()

    def players(self) -> List[Player]:  # pragma: no cover
        return self._players

    def selected_team(self) -> Optional[ClubTeam]:  # pragma: no cover
        items = self._team_list.selectedItems()
        if not items:
            return None
        return items[0].data(Qt.ItemDataRole.UserRole)


__all__ = ["TeamSelectionDialog"]
