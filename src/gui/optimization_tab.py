"""Optimization tab UI providing basic lineup optimization interface."""

from __future__ import annotations
from typing import List
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QSpinBox,
    QComboBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QProgressBar,
    QMessageBox,
)
from PyQt6.QtCore import Qt

from data.player import Player
from optimization.optimizer import optimize_lineup


class OptimizationTab(QWidget):  # pragma: no cover - GUI heavy
    def __init__(self, players_provider=None, parent=None) -> None:
        super().__init__(parent)
        # players_provider: callable returning current player list (optional)
        self._players_provider = players_provider or (lambda: [])
        layout = QVBoxLayout(self)
        controls = QHBoxLayout()
        controls.addWidget(QLabel("Lineup Size:"))
        self._size = QSpinBox()
        self._size.setRange(1, 20)
        self._size.setValue(4)
        controls.addWidget(self._size)
        controls.addWidget(QLabel("Objective:"))
        self._objective = QComboBox()
        self._objective.addItems(["qttr_max", "balance"])
        controls.addWidget(self._objective)
        self._btn_run = QPushButton("Run Optimization")
        controls.addWidget(self._btn_run)
        controls.addStretch(1)
        layout.addLayout(controls)
        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        layout.addWidget(self._progress)
        self._results = QTableWidget(0, 3)
        self._results.setHorizontalHeaderLabels(["Name", "Team", "Q-TTR"])
        layout.addWidget(self._results)
        self._summary = QLabel("Ready")
        layout.addWidget(self._summary)
        self._btn_run.clicked.connect(self._on_run)

    def _current_players(self) -> List[Player]:
        try:
            players = self._players_provider() or []
        except Exception:
            players = []
        return players

    def _on_run(self):  # pragma: no cover - GUI interaction
        players = self._current_players()
        if not players:
            QMessageBox.information(self, "Optimization", "No players available.")
            return
        size = self._size.value()
        if size > len(players):
            QMessageBox.warning(self, "Optimization", "Size exceeds available players.")
            return
        obj = self._objective.currentText()  # type: ignore
        # Simulate progress for now (instant computation but set bar sequence)
        self._progress.setValue(0)
        try:
            result = optimize_lineup(players, size=size, objective=obj)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, "Optimization", f"Failed: {exc}")
            return
        self._progress.setValue(100)
        self._populate_results(result.players)
        self._summary.setText(
            f"Objective: {result.objective} | Total: {result.total_qttr} | Avg: {result.average_qttr:.1f} | Spread: {result.spread}"
        )

    def _populate_results(self, players: List[Player]):
        self._results.setRowCount(0)
        for p in players:
            row = self._results.rowCount()
            self._results.insertRow(row)
            self._results.setItem(row, 0, QTableWidgetItem(p.name))
            self._results.setItem(row, 1, QTableWidgetItem(p.team or ""))
            self._results.setItem(row, 2, QTableWidgetItem(str(p.q_ttr)))


__all__ = ["OptimizationTab"]
