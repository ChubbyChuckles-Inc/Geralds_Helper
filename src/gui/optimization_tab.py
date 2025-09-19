"""Optimization tab UI providing basic lineup optimization interface."""

from __future__ import annotations
from typing import List, Callable
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
    QDateEdit,
    QFileDialog,
    QLineEdit,
    QCheckBox,
    QDialog,
    QTextEdit,
)
from PyQt6.QtCore import Qt, QDate

from data.player import Player
from optimization.optimizer import optimize_lineup
from optimization.scenario import ScenarioResult, export_markdown
from optimization.report import build_report
from optimization.what_if import run_what_if_scenarios
from pathlib import Path
import json


class OptimizationTab(QWidget):  # pragma: no cover - GUI heavy
    def __init__(self, players_provider=None, parent=None) -> None:
        super().__init__(parent)
        # players_provider: callable returning current player list (optional)
        self._players_provider = players_provider or (lambda: [])
        self._history: List[ScenarioResult] = []
        self._next_id = 1
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
        controls.addWidget(QLabel("Avail Date:"))
        self._avail_date = QDateEdit()
        self._avail_date.setCalendarPopup(True)
        self._avail_date.setDate(QDate.currentDate())
        controls.addWidget(self._avail_date)
        self._btn_run = QPushButton("Run Optimization")
        self._auto_rerun = QCheckBox("Auto Re-run")
        controls.addWidget(self._btn_run)
        controls.addWidget(self._auto_rerun)
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
        # History / actions section
        history_bar = QHBoxLayout()
        self._btn_export_history = QPushButton("Export History")
        self._btn_generate_report = QPushButton("Generate Report")
        self._btn_clear_history = QPushButton("Clear History")
        self._btn_save_preset = QPushButton("Save Preset")
        self._btn_load_preset = QPushButton("Load Preset")
        history_bar.addWidget(self._btn_export_history)
        history_bar.addWidget(self._btn_clear_history)
        history_bar.addWidget(self._btn_generate_report)
        history_bar.addWidget(self._btn_save_preset)
        history_bar.addWidget(self._btn_load_preset)
        history_bar.addStretch(1)
        layout.addLayout(history_bar)
        self._history_table = QTableWidget(0, 9)
        self._history_table.setHorizontalHeaderLabels(
            [
                "ID",
                "Time",
                "Obj",
                "Size",
                "Total",
                "Avg",
                "Spread",
                "BestDelta",
                "Scenario",
            ]
        )
        layout.addWidget(self._history_table)
        # What-if scenarios
        what_if_bar = QHBoxLayout()
        self._btn_what_if = QPushButton("Run What-If…")
        what_if_bar.addWidget(self._btn_what_if)
        what_if_bar.addStretch(1)
        layout.addLayout(what_if_bar)
        self._btn_run.clicked.connect(self._on_run)
        self._btn_export_history.clicked.connect(self._on_export_history)
        self._btn_clear_history.clicked.connect(self._on_clear_history)
        self._btn_generate_report.clicked.connect(self._on_generate_report)
        self._btn_save_preset.clicked.connect(self._on_save_preset)
        self._btn_load_preset.clicked.connect(self._on_load_preset)
        self._btn_what_if.clicked.connect(self._on_what_if)
        self._auto_rerun.stateChanged.connect(lambda _s: None)  # placeholder
        # react to availability date change for auto re-run
        self._avail_date.dateChanged.connect(self._maybe_auto_rerun)
        self._presets_path = Path("config/optimization_presets.json")

    def _current_players(self) -> List[Player]:
        try:
            players = self._players_provider() or []
        except Exception:
            players = []
        # Availability filter by date
        d_iso = self._avail_date.date().toPyDate().isoformat()
        filtered = []
        for p in players:
            if not p.availability or d_iso in p.availability:
                filtered.append(p)
        return filtered

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
        self._append_history(size=size, result=result)

    def _populate_results(self, players: List[Player]):
        self._results.setRowCount(0)
        for p in players:
            row = self._results.rowCount()
            self._results.insertRow(row)
            self._results.setItem(row, 0, QTableWidgetItem(p.name))
            self._results.setItem(row, 1, QTableWidgetItem(p.team or ""))
            self._results.setItem(row, 2, QTableWidgetItem(str(p.q_ttr)))

    def _append_history(
        self, size: int, result, scenario_name: str | None = None
    ):  # result is LineupResult
        s = ScenarioResult.from_lineup(self._next_id, size=size, result=result)
        if scenario_name:
            s.scenario_name = scenario_name
        self._next_id += 1
        self._history.append(s)
        self._history_table.insertRow(self._history_table.rowCount())
        # Determine current best total to compute delta display
        best_total = min((h.total_qttr for h in self._history), default=None)
        # For objective qttr_max we want highest total (so delta vs max); adjust logic
        if s.objective == "qttr_max":
            best_total = max((h.total_qttr for h in self._history), default=None)
        for col, val in enumerate(s.to_row(best_total=best_total)):
            self._history_table.setItem(
                self._history_table.rowCount() - 1, col, QTableWidgetItem(val)
            )

    def _on_export_history(self):  # pragma: no cover - GUI interaction
        if not self._history:
            QMessageBox.information(self, "Export", "No history to export.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Optimization History", "optimization_history.md", "Markdown (*.md)"
        )
        if not path:
            return
        content = export_markdown(self._history)
        Path(path).write_text(content, encoding="utf-8")

    def _on_clear_history(self):  # pragma: no cover
        self._history.clear()
        self._history_table.setRowCount(0)

    def _on_generate_report(self):  # pragma: no cover - GUI interaction
        if not self._history:
            QMessageBox.information(self, "Report", "No scenarios to report.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Optimization Report", "optimization_report.md", "Markdown (*.md)"
        )
        if not path:
            return
        report = build_report(self._history)
        Path(path).write_text(report, encoding="utf-8")
        QMessageBox.information(self, "Report", "Report generated.")

    def _on_save_preset(self):  # pragma: no cover
        # simple preset structure: {"size": int, "objective": str}
        preset = {"size": self._size.value(), "objective": self._objective.currentText()}
        presets = []
        if self._presets_path.exists():
            try:
                presets = json.loads(self._presets_path.read_text(encoding="utf-8"))
            except Exception:
                presets = []
        presets.append(preset)
        self._presets_path.parent.mkdir(parents=True, exist_ok=True)
        self._presets_path.write_text(json.dumps(presets, indent=2), encoding="utf-8")
        QMessageBox.information(self, "Preset", "Preset saved.")

    def _on_load_preset(self):  # pragma: no cover
        if not self._presets_path.exists():
            QMessageBox.information(self, "Preset", "No presets file found.")
            return
        try:
            presets = json.loads(self._presets_path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, "Preset", f"Failed to load: {exc}")
            return
        if not presets:
            QMessageBox.information(self, "Preset", "No presets stored.")
            return
        p = presets[-1]  # simplest: take last
        self._size.setValue(int(p.get("size", self._size.value())))
        obj = str(p.get("objective", self._objective.currentText()))
        idx = self._objective.findText(obj)
        if idx >= 0:
            self._objective.setCurrentIndex(idx)
        QMessageBox.information(self, "Preset", "Last preset loaded.")

    # --- What-if scenarios ---
    def _on_what_if(self):  # pragma: no cover - GUI assembly
        dlg = QDialog(self)
        dlg.setWindowTitle("What-If Scenarios")
        v = QVBoxLayout(dlg)
        info = QLabel(
            "Enter scenarios (one per line). Format: name | exclude=name1,name2 (names case-insensitive).\n"
            "Example: No Top | exclude=Alice,Bob"
        )
        info.setWordWrap(True)
        v.addWidget(info)
        txt = QTextEdit()
        v.addWidget(txt)
        btns = QHBoxLayout()
        run_btn = QPushButton("Run")
        cancel_btn = QPushButton("Cancel")
        btns.addWidget(run_btn)
        btns.addWidget(cancel_btn)
        btns.addStretch(1)
        v.addLayout(btns)
        run_btn.clicked.connect(lambda: (self._exec_what_if(txt.toPlainText()), dlg.accept()))
        cancel_btn.clicked.connect(dlg.reject)
        dlg.exec()

    def _exec_what_if(self, text: str):  # pragma: no cover - uses GUI state
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        if not lines:
            return
        scenarios = []
        for line in lines:
            name = line
            excl = []
            if "|" in line:
                left, right = [s.strip() for s in line.split("|", 1)]
                name = left or name
                if right.lower().startswith("exclude="):
                    excl_part = right.split("=", 1)[1]
                    excl = [x.strip() for x in excl_part.split(",") if x.strip()]
            scenarios.append({"name": name, "exclude_names": excl})
        players = self._current_players()
        avail_date = self._avail_date.date().toPyDate().isoformat()
        base_next = self._next_id
        results = run_what_if_scenarios(
            players,
            scenarios,
            size=self._size.value(),
            objective=self._objective.currentText(),
            availability_date=avail_date,
            start_id=base_next,
        )
        for r in results:
            # compute best total contextually again inside append helper
            # but we already assigned IDs sequentially.
            self._history.append(r)
            self._history_table.insertRow(self._history_table.rowCount())
            best_total = min((h.total_qttr for h in self._history), default=None)
            if r.objective == "qttr_max":
                best_total = max((h.total_qttr for h in self._history), default=None)
            for col, val in enumerate(r.to_row(best_total=best_total)):
                self._history_table.setItem(
                    self._history_table.rowCount() - 1, col, QTableWidgetItem(val)
                )
        self._next_id = max(self._next_id, (results[-1].id + 1) if results else self._next_id)

    def _maybe_auto_rerun(self):  # pragma: no cover - GUI
        if self._auto_rerun.isChecked():
            self._on_run()

    # Public helper so other tabs (e.g., PlayersTab) can notify changes
    def notify_players_changed(self):  # pragma: no cover - GUI
        self._maybe_auto_rerun()


__all__ = ["OptimizationTab"]
