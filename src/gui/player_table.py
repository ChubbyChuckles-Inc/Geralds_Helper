"""Player table widget with inline editing."""

from __future__ import annotations

from typing import List

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem

from data.player import Player


class PlayerTable(QTableWidget):
    HEADERS = ["Name", "Team", "Q-TTR", "Avail Days"]

    def __init__(self, players: list[Player] | None = None) -> None:
        super().__init__(0, len(self.HEADERS))
        self._players: list[Player] = players or []
        self.setHorizontalHeaderLabels(self.HEADERS)
        # Keep sorting disabled for predictable row indices in tests & filtering; can enable later if needed.
        self.setSortingEnabled(False)
        # Drag & drop internal movement to reassign teams via drop row's team
        self.setDragDropMode(QTableWidget.DragDropMode.InternalMove)
        # Allow extended selection for bulk operations
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self._refresh()
        self.cellChanged.connect(self._on_cell_changed)

    # --- Data operations -------------------------------------------------
    def players(self) -> list[Player]:
        return [p.clone() for p in self._players]

    def set_players(self, players: list[Player]) -> None:
        self._players = [p.clone() for p in players]
        self._refresh()

    def add_player(self, player: Player) -> None:
        self._players.append(player.clone())
        self._append_row(player)

    def filter(self, text: str) -> None:
        """Filter rows by substring in name or team (case-insensitive).

        Empty text shows all rows.
        """
        t = text.lower().strip()
        for row in range(self.rowCount()):
            name_item = self.item(row, 0)
            team_item = self.item(row, 1)
            if name_item is None or team_item is None:
                continue
            if not t:
                self.setRowHidden(row, False)
                continue
            name = name_item.text().lower()
            team = team_item.text().lower()
            match = (t in name) or (t in team)
            self.setRowHidden(row, not match)

    # --- Internal helpers ------------------------------------------------
    def _refresh(self) -> None:
        self.setRowCount(0)
        for p in self._players:
            self._append_row(p)

    def _append_row(self, p: Player) -> None:
        row = self.rowCount()
        self.insertRow(row)
        self.setItem(row, 0, QTableWidgetItem(p.name))
        self.setItem(row, 1, QTableWidgetItem(p.team or ""))
        q_ttr_item = QTableWidgetItem(str(p.q_ttr))
        q_ttr_item.setData(Qt.ItemDataRole.EditRole, p.q_ttr)
        self.setItem(row, 2, q_ttr_item)
        avail_count = QTableWidgetItem(str(len(p.availability)))
        avail_count.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
        self.setItem(row, 3, avail_count)

    def _on_cell_changed(self, row: int, col: int) -> None:  # pragma: no cover (simple)
        if row >= len(self._players):
            return
        player = self._players[row]
        if col == 0:
            player.name = self.item(row, col).text()
        elif col == 1:
            player.team = self.item(row, col).text() or None
        elif col == 2:
            try:
                player.q_ttr = int(self.item(row, col).text())
            except ValueError:
                pass
        # Recompute availability cell (in case of future edits via external dialogs)
        if col != 3 and row < self.rowCount():
            avail_item = self.item(row, 3)
            if avail_item:
                avail_item.setText(str(len(player.availability)))

    # --- Bulk / utility operations --------------------------------------
    def selected_players(self) -> list[Player]:
        rows = {idx.row() for idx in self.selectionModel().selectedRows()}
        return [self._players[r] for r in rows if r < len(self._players)]

    def bulk_set_team(self, team: str | None) -> None:
        for p in self.selected_players():
            p.team = team
        self._refresh()

    def dropEvent(self, event):  # pragma: no cover - GUI interaction
        # After internal move, re-align players list with new visual order
        super().dropEvent(event)
        new_players: list[Player] = []
        for row in range(self.rowCount()):
            # match by name + q_ttr + team (simple heuristic)
            name = self.item(row, 0).text()
            team = self.item(row, 1).text() or None
            q_ttr = int(self.item(row, 2).text())
            # find in old list
            for p in self._players:
                if p.name == name and p.q_ttr == q_ttr and (p.team or "") == (team or ""):
                    new_players.append(p)
                    break
        if len(new_players) == len(self._players):
            self._players = new_players


__all__ = ["PlayerTable"]
