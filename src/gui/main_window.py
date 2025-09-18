"""Main application window implementation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QAction, QCloseEvent
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QTabWidget,
    QVBoxLayout,
    QLabel,
    QStatusBar,
    QMenuBar,
    QFileDialog,
    QMessageBox,
)

from config.app_settings import load_settings, CONFIG_FILE


class MainWindow(QMainWindow):
    """Primary application window with tabbed interface and basic actions."""

    def __init__(self) -> None:
        super().__init__()
        self.settings = load_settings()
        self.setWindowTitle("Table Tennis Team Manager")
        self.resize(self.settings.window_width, self.settings.window_height)
        self._tabs = QTabWidget()
        self._tabs.setDocumentMode(True)
        self._tabs.setMovable(True)
        self._init_tabs()
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.addWidget(self._tabs)
        self.setCentralWidget(container)
        self._create_menu()
        self._create_status_bar()

    # ----- UI Composition -------------------------------------------------
    def _init_tabs(self) -> None:
        self._add_tab("Players", QLabel("Player management coming soon."))
        self._add_tab("Matches", QLabel("Match scheduling coming soon."))
        self._add_tab("Optimization", QLabel("Optimization tools coming soon."))

    def _add_tab(self, name: str, widget: QWidget) -> None:
        self._tabs.addTab(widget, name)

    def _create_menu(self) -> None:
        menubar = self.menuBar()  # type: QMenuBar
        file_menu = menubar.addMenu("&File")
        view_menu = menubar.addMenu("&View")
        help_menu = menubar.addMenu("&Help")

        act_exit = QAction("E&xit", self)
        act_exit.setShortcut("Ctrl+Q")
        act_exit.triggered.connect(self.close)
        file_menu.addAction(act_exit)

        act_open_config = QAction("Open Config…", self)
        act_open_config.triggered.connect(self._open_config)
        file_menu.addAction(act_open_config)

        act_about = QAction("About", self)
        act_about.triggered.connect(self._show_about)
        help_menu.addAction(act_about)

    def _create_status_bar(self) -> None:
        status = QStatusBar()
        status.showMessage("Ready")
        self.setStatusBar(status)

    # ----- Actions --------------------------------------------------------
    def _open_config(self) -> None:  # pragma: no cover - GUI interaction
        dlg = QFileDialog(self, "Open Config File")
        dlg.setFileMode(QFileDialog.FileMode.ExistingFile)
        dlg.setNameFilter("JSON Files (*.json)")
        dlg.setDirectory(str(CONFIG_FILE.parent))
        dlg.exec()

    def _show_about(self) -> None:  # pragma: no cover - GUI interaction
        QMessageBox.information(
            self,
            "About",
            "Table Tennis Team Manager\nEarly GUI Framework Preview",
        )

    # ----- Persistence ----------------------------------------------------
    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        self._persist_window_state()
        super().closeEvent(event)

    def _persist_window_state(self) -> None:
        try:
            data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            data = {}
        g = self.geometry()
        data.setdefault("window", {})
        data["window"].update({"width": g.width(), "height": g.height()})
        CONFIG_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")

    # ----- Introspection for tests ---------------------------------------
    def tab_names(self) -> list[str]:
        return [self._tabs.tabText(i) for i in range(self._tabs.count())]


__all__ = ["MainWindow"]
