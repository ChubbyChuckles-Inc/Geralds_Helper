"""Dialogs related to player management."""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QDialogButtonBox,
    QMessageBox,
)

from data.player import Player


class AddPlayerDialog(QDialog):
    def __init__(self, parent=None) -> None:  # type: ignore
        super().__init__(parent)
        self.setWindowTitle("Add Player")
        self._name = QLineEdit()
        self._team = QLineEdit()
        self._q_ttr = QLineEdit()
        form = QFormLayout()
        form.addRow("Name", self._name)
        form.addRow("Team", self._team)
        form.addRow("Q-TTR", self._q_ttr)
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self._on_ok)
        btns.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(btns)
        self._player: Player | None = None

    def _on_ok(self) -> None:
        name = self._name.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation", "Name is required")
            return
        try:
            q_ttr = int(self._q_ttr.text().strip() or 0)
        except ValueError:
            QMessageBox.warning(self, "Validation", "Q-TTR must be an integer")
            return
        team = self._team.text().strip() or None
        self._player = Player(name=name, q_ttr=q_ttr, team=team)
        self.accept()

    def player(self) -> Player | None:
        return self._player


__all__ = ["AddPlayerDialog"]
