"""Raycast-style command palette — pages, actions, and experiments."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent, QShowEvent
from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from quantlab.ui.command_registry import PaletteCommand, filter_palette_commands


class CommandPalette(QDialog):
    def __init__(
        self,
        commands: list[PaletteCommand],
        *,
        recents: list[str] | None = None,
        on_nav: Callable[[str], None],
        on_action: Callable[[str], None],
        on_experiment: Callable[[str], None],
        on_command_run: Callable[[str], None] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._commands = commands
        self._recents = list(recents or [])
        self._on_nav = on_nav
        self._on_action = on_action
        self._on_experiment = on_experiment
        self._on_command_run = on_command_run
        self.setWindowTitle("Command palette")
        self.setModal(True)
        self.resize(560, 420)

        layout = QVBoxLayout(self)
        hint = QLabel(
            "↑↓ navigate · Enter run · Esc close · Recent commands shown when empty"
        )
        hint.setObjectName("nayakVoice")
        self._search = QLineEdit()
        self._search.setPlaceholderText("backtest · portfolio · run validation · open experiment…")
        self._list = QListWidget()
        layout.addWidget(hint)
        layout.addWidget(self._search)
        layout.addWidget(self._list, 1)

        self._search.textChanged.connect(self._repopulate)
        self._list.itemActivated.connect(self._activate)
        self._search.returnPressed.connect(self._activate_current)
        self._repopulate("")

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        self._search.setFocus()
        self._search.selectAll()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        key = event.key()
        if key == Qt.Key.Key_Escape:
            self.reject()
            return
        if key in {Qt.Key.Key_Down, Qt.Key.Key_Up}:
            row = self._list.currentRow()
            if key == Qt.Key.Key_Down and row < self._list.count() - 1:
                self._list.setCurrentRow(row + 1)
            elif key == Qt.Key.Key_Up and row > 0:
                self._list.setCurrentRow(row - 1)
            elif key == Qt.Key.Key_Down and row < 0 and self._list.count():
                self._list.setCurrentRow(0)
            event.accept()
            return
        super().keyPressEvent(event)

    def _repopulate(self, query: str) -> None:
        visible = filter_palette_commands(
            self._commands,
            query,
            recents=self._recents if not query.strip() else None,
        )
        self._list.clear()
        recent_set = set(self._recents)
        for cmd in visible[:40]:
            row = QListWidgetItem(cmd.title)
            row.setData(Qt.ItemDataRole.UserRole, cmd.command_id)
            row.setData(Qt.ItemDataRole.UserRole + 1, cmd.kind)
            kind = {"nav": "Page", "action": "Action", "experiment": "Experiment"}[cmd.kind]
            prefix = "Recent · " if cmd.command_id in recent_set and not query.strip() else ""
            row.setText(f"{prefix}{cmd.title}    · {kind}")
            row.setToolTip(cmd.subtitle)
            self._list.addItem(row)
        if self._list.count():
            self._list.setCurrentRow(0)

    def _activate(self, item: QListWidgetItem) -> None:
        command_id = item.data(Qt.ItemDataRole.UserRole)
        kind = item.data(Qt.ItemDataRole.UserRole + 1)
        if not command_id:
            return
        cid = str(command_id)
        if self._on_command_run is not None:
            self._on_command_run(cid)
        if kind == "nav" and cid.startswith("nav:"):
            self._on_nav(cid.removeprefix("nav:"))
        elif kind == "action" and cid.startswith("action:"):
            self._on_action(cid.removeprefix("action:"))
        elif kind == "experiment" and cid.startswith("experiment:"):
            self._on_experiment(cid.removeprefix("experiment:"))
        self.accept()

    def _activate_current(self) -> None:
        item = self._list.currentItem()
        if item is not None:
            self._activate(item)
