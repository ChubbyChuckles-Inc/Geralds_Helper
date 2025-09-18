"""Main application window implementation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional, List

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
    QHBoxLayout,
    QPushButton,
    QLineEdit,
)

from config.app_settings import load_settings, CONFIG_FILE
from data.player import Player
from gui.player_table import PlayerTable
from gui.player_dialogs import AddPlayerDialog


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
        self._add_tab("Players", self._build_players_tab())
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

    # ----- Players Tab ---------------------------------------------------
    def _build_players_tab(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        toolbar = QHBoxLayout()
        self._player_search = QLineEdit()
        self._player_search.setPlaceholderText("Search players…")
        btn_add = QPushButton("Add")
        btn_export = QPushButton("Export JSON")
        btn_import = QPushButton("Import JSON")
        toolbar.addWidget(self._player_search)
        toolbar.addWidget(btn_add)
        toolbar.addWidget(btn_export)
        toolbar.addWidget(btn_import)
        layout.addLayout(toolbar)
        self._player_table = PlayerTable([])
        layout.addWidget(self._player_table)
        self._wire_player_tab(btn_add, btn_export, btn_import)
        return container

    def _wire_player_tab(
        self, btn_add: QPushButton, btn_export: QPushButton, btn_import: QPushButton
    ) -> None:
        self._player_search.textChanged.connect(self._player_table.filter)
        btn_add.clicked.connect(self._on_add_player)
        btn_export.clicked.connect(self._on_export_players)
        btn_import.clicked.connect(self._on_import_players)

    # Actions
    def _on_add_player(self) -> None:  # pragma: no cover - dialog
        dlg = AddPlayerDialog(self)
        if dlg.exec():
            p = dlg.player()
            if p:
                self._player_table.add_player(p)

    def _on_export_players(self) -> None:  # pragma: no cover - dialog
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Players", "players.json", "JSON (*.json)"
        )
        if path:
            from data.serialization import save_players_json

            save_players_json(self._player_table.players(), Path(path))

    def _on_import_players(self) -> None:  # pragma: no cover - dialog
        path, _ = QFileDialog.getOpenFileName(self, "Import Players", "", "JSON (*.json)")
        if path:
            from data.serialization import load_players_json

            try:
                players = load_players_json(Path(path))
            except Exception as exc:  # noqa: BLE001
                QMessageBox.warning(self, "Import", f"Failed to import players: {exc}")
                return
            self._player_table.set_players(players)

    # ----- Introspection for tests ---------------------------------------
    def tab_names(self) -> list[str]:
        return [self._tabs.tabText(i) for i in range(self._tabs.count())]


__all__ = ["MainWindow"]
