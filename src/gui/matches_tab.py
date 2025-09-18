"""Matches tab UI implementation."""

from __future__ import annotations
from datetime import date
from pathlib import Path
from typing import List

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QCalendarWidget,
    QTableWidget,
    QTableWidgetItem,
    QFileDialog,
    QMessageBox,
    QDialog,
    QFormLayout,
    QLineEdit,
    QDialogButtonBox,
    QCheckBox,
)

from data.match import Match, detect_conflicts
import json


class MatchDialog(QDialog):  # pragma: no cover - GUI interaction
    def __init__(self, parent=None, match: Match | None = None):
        super().__init__(parent)
        self.setWindowTitle("Match")
        self._match = match.clone() if match else Match()
        layout = QFormLayout(self)
        self._home = QLineEdit(self._match.home_team)
        self._away = QLineEdit(self._match.away_team)
        self._location = QLineEdit(self._match.location)
        self._notes = QLineEdit(self._match.notes)
        self._home_score = QLineEdit(
            "" if self._match.home_score is None else str(self._match.home_score)
        )
        self._away_score = QLineEdit(
            "" if self._match.away_score is None else str(self._match.away_score)
        )
        self._completed = QCheckBox()
        self._completed.setChecked(self._match.completed)
        layout.addRow("Home Team", self._home)
        layout.addRow("Away Team", self._away)
        layout.addRow("Location", self._location)
        layout.addRow("Notes", self._notes)
        layout.addRow("Home Score", self._home_score)
        layout.addRow("Away Score", self._away_score)
        layout.addRow("Completed", self._completed)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def match(self) -> Match:
        self._match.home_team = self._home.text().strip()
        self._match.away_team = self._away.text().strip()
        self._match.location = self._location.text().strip()
        self._match.notes = self._notes.text().strip()
        # parse scores
        try:
            self._match.home_score = int(self._home_score.text().strip()) if self._home_score.text().strip() else None
        except ValueError:
            self._match.home_score = None
        try:
            self._match.away_score = int(self._away_score.text().strip()) if self._away_score.text().strip() else None
        except ValueError:
            self._match.away_score = None
        self._match.completed = self._completed.isChecked()
        return self._match


class MatchesTab(QWidget):  # pragma: no cover - heavy GUI
    def __init__(self, parent=None):
        super().__init__(parent)
        self._matches: List[Match] = []
        layout = QVBoxLayout(self)
        toolbar = QHBoxLayout()
        filter_bar = QHBoxLayout()
        self._search = QLineEdit()
        self._search.setPlaceholderText("Search team/location/notes…")
        self._all_dates = QCheckBox("All Dates")
        filter_bar.addWidget(self._search)
        filter_bar.addWidget(self._all_dates)
        layout.addLayout(filter_bar)
        btn_add = QPushButton("Add")
        btn_edit = QPushButton("Edit")
        btn_delete = QPushButton("Delete")
        btn_export = QPushButton("Export JSON")
        btn_import = QPushButton("Import JSON")
        toolbar.addWidget(btn_add)
        toolbar.addWidget(btn_edit)
        toolbar.addWidget(btn_delete)
        toolbar.addWidget(btn_export)
        toolbar.addWidget(btn_import)
        layout.addLayout(toolbar)
        body = QHBoxLayout()
        self._calendar = QCalendarWidget()
        self._calendar.selectionChanged.connect(self._on_date)
        body.addWidget(self._calendar, 1)
        self._table = QTableWidget(0, 8)
        self._table.setHorizontalHeaderLabels(
            ["Date", "Home", "Away", "Loc", "Notes", "H", "A", "Done"]
        )
        self._table.itemDoubleClicked.connect(self._on_edit)
        body.addWidget(self._table, 2)
        layout.addLayout(body)
        # wiring
        btn_add.clicked.connect(self._on_add)
        btn_edit.clicked.connect(self._on_edit)
        btn_delete.clicked.connect(self._on_delete)
        btn_export.clicked.connect(self._on_export)
        btn_import.clicked.connect(self._on_import)
        self._search.textChanged.connect(self._refresh)
        self._all_dates.stateChanged.connect(self._refresh)

    # Data helpers
    def _refresh(self):
        self._table.setRowCount(0)
        # filter by selected date for brevity
        sel = self._calendar.selectedDate().toPyDate().isoformat()
        if self._all_dates.isChecked():
            day_matches = list(self._matches)
        else:
            day_matches = [m for m in self._matches if m.match_date.isoformat() == sel]
        q = self._search.text().lower().strip()
        if q:
            def match_filter(m: Match) -> bool:
                return (
                    q in m.home_team.lower()
                    or q in m.away_team.lower()
                    or q in m.location.lower()
                    or q in m.notes.lower()
                )
            day_matches = [m for m in day_matches if match_filter(m)]
        for m in day_matches:
            row = self._table.rowCount()
            self._table.insertRow(row)
            self._table.setItem(row, 0, QTableWidgetItem(m.match_date.isoformat()))
            self._table.setItem(row, 1, QTableWidgetItem(m.home_team))
            self._table.setItem(row, 2, QTableWidgetItem(m.away_team))
            self._table.setItem(row, 3, QTableWidgetItem(m.location))
            self._table.setItem(row, 4, QTableWidgetItem(m.notes))
            self._table.setItem(row, 5, QTableWidgetItem("" if m.home_score is None else str(m.home_score)))
            self._table.setItem(row, 6, QTableWidgetItem("" if m.away_score is None else str(m.away_score)))
            self._table.setItem(row, 7, QTableWidgetItem("Y" if m.completed else ""))
        # highlight conflicts (simple: duplicate team on same date)
        conflicts = detect_conflicts(self._matches)
        conflict_ids = {cid for pair in conflicts for cid in pair}
        if conflicts:
            self.setToolTip(f"Conflicts detected: {len(conflicts)}")
        else:
            self.setToolTip("")
        # Basic highlight by appending * to notes
        for row in range(self._table.rowCount()):
            date_item = self._table.item(row, 0)
            home_item = self._table.item(row, 1)
            away_item = self._table.item(row, 2)
            for m in self._matches:
                if (
                    m.match_date.isoformat() == date_item.text()
                    and m.home_team == home_item.text()
                    and m.away_team == away_item.text()
                    and m.id in conflict_ids
                ):
                    notes_item = self._table.item(row, 4)
                    notes_item.setText((notes_item.text() or "") + " *conflict*")

    def _selected_match(self) -> Match | None:
        rows = self._table.selectionModel().selectedRows()
        if not rows:
            return None
        row = rows[0].row()
        # retrieve by matching fields
        date_str = self._table.item(row, 0).text()
        home = self._table.item(row, 1).text()
        away = self._table.item(row, 2).text()
        for m in self._matches:
            if m.match_date.isoformat() == date_str and m.home_team == home and m.away_team == away:
                return m
        return None

    # Slots
    def _on_date(self):
        self._refresh()

    def _on_add(self):
        dlg = MatchDialog(self)
        if dlg.exec():
            m = dlg.match()
            m.match_date = self._calendar.selectedDate().toPyDate()
            self._matches.append(m)
            self._refresh()

    def _on_edit(self):
        m = self._selected_match()
        if not m:
            return
        dlg = MatchDialog(self, m)
        if dlg.exec():
            updated = dlg.match()
            # keep id & date
            m.home_team = updated.home_team
            m.away_team = updated.away_team
            m.location = updated.location
            m.notes = updated.notes
            self._refresh()

    def _on_delete(self):
        m = self._selected_match()
        if not m:
            return
        self._matches = [mm for mm in self._matches if mm.id != m.id]
        self._refresh()

    def _on_export(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Matches", "matches.json", "JSON (*.json)"
        )
        if not path:
            return
        data = [m.to_dict() for m in self._matches]
        Path(path).write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _on_import(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import Matches", "", "JSON (*.json)")
        if not path:
            return
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
            self._matches = [Match.from_dict(d) for d in data]
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, "Import", f"Failed: {exc}")
        self._refresh()

    # For tests
    def add_match(self, match: Match):
        self._matches.append(match.clone())
        self._refresh()

    def matches(self) -> List[Match]:
        return [m.clone() for m in self._matches]


__all__ = ["MatchesTab", "MatchDialog"]
