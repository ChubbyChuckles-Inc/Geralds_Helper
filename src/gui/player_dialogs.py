"""Dialogs related to player management."""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QDialogButtonBox,
    QMessageBox,
    QPushButton,
    QFileDialog,
    QLabel,
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


class PlayerProfileDialog(QDialog):
    """Edit existing player attributes including photo path."""

    def __init__(self, player: Player, parent=None) -> None:  # type: ignore
        super().__init__(parent)
        self.setWindowTitle(f"Profile - {player.name}")
        self._player = player
        self._name = QLineEdit(player.name)
        self._team = QLineEdit(player.team or "")
        self._q_ttr = QLineEdit(str(player.q_ttr))
        self._photo_label = QLabel(player.photo_path or "(no photo)")
        btn_photo = QPushButton("Choose Photo…")
        btn_photo.clicked.connect(self._choose_photo)  # type: ignore[arg-type]
        form = QFormLayout()
        form.addRow("Name", self._name)
        form.addRow("Team", self._team)
        form.addRow("Q-TTR", self._q_ttr)
        form.addRow("Photo", btn_photo)
        form.addRow("Photo Path", self._photo_label)
        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self._on_ok)
        btns.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(btns)

    def _choose_photo(self) -> None:  # pragma: no cover - dialog
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Photo", "", "Images (*.png *.jpg *.jpeg)"
        )
        if path:
            self._photo_label.setText(path)

    def _on_ok(self) -> None:
        name = self._name.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation", "Name is required")
            return
        try:
            q_ttr = int(self._q_ttr.text().strip())
        except ValueError:
            QMessageBox.warning(self, "Validation", "Q-TTR must be an integer")
            return
        self._player.name = name
        self._player.team = self._team.text().strip() or None
        self._player.q_ttr = q_ttr
        photo = self._photo_label.text().strip()
        self._player.photo_path = photo if photo and photo != "(no photo)" else None
        self.accept()


__all__ = ["AddPlayerDialog", "PlayerProfileDialog"]
