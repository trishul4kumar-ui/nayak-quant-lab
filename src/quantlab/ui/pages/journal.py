from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from quantlab.app.assistant import JournalEntry, NayakAssistant
from quantlab.app.bootstrap import ApplicationRuntime
from quantlab.ui.widgets.journal_calendar import JournalCalendarWidget
from quantlab.ui.widgets.lab_shell import LabPageShell


class JournalPage(LabPageShell):
    def __init__(
        self,
        runtime: ApplicationRuntime,
        *,
        on_open_full: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(
            "Lab journal",
            subtitle="Click a run, write what you learned — research memory, not trade advice.",
        )
        self._runtime = runtime
        self._assistant = NayakAssistant(runtime)
        self._on_open_full = on_open_full
        self._entries: list[JournalEntry] = []
        self._selected_id: str | None = None

        if on_open_full is not None:
            btn = QPushButton("Open in Full Lab →")
            btn.clicked.connect(on_open_full)
            self.add_toolbar_widget(btn)

        split = QSplitter(Qt.Orientation.Horizontal)
        self._list = QListWidget()
        self._list.setObjectName("journalList")
        self._list.currentRowChanged.connect(self._on_row_changed)
        self._calendar = JournalCalendarWidget()
        self._calendar.day_selected.connect(self._on_calendar_day)
        list_tab = QWidget()
        list_layout = QVBoxLayout(list_tab)
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_layout.addWidget(self._list)
        self._tabs = QTabWidget()
        self._tabs.addTab(list_tab, "List")
        self._tabs.addTab(self._calendar, "Calendar")
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(self._tabs)
        right = QWidget()
        right_layout = QVBoxLayout(right)
        self._detail = QPlainTextEdit()
        self._detail.setPlaceholderText("What did this run teach you?")
        save = QPushButton("Save note")
        save.setObjectName("primary")
        save.clicked.connect(self._save_note)
        self._saved = QLabel()
        self._saved.setObjectName("nayakVoice")
        right_layout.addWidget(self._detail, 1)
        row = QHBoxLayout()
        row.addWidget(save)
        row.addWidget(self._saved)
        row.addStretch()
        right_layout.addLayout(row)
        split.addWidget(left)
        split.addWidget(right)
        self.body().addWidget(split, 1)
        self.refresh()

    def select_experiment(self, experiment_id: str) -> None:
        for i, entry in enumerate(self._entries):
            if entry.experiment_id == experiment_id:
                self._list.setCurrentRow(i)
                return

    def refresh(self) -> None:
        from PySide6.QtWidgets import QListWidgetItem

        self._entries = self._assistant.journal_entries()
        self._list.clear()
        for entry in self._entries:
            item = QListWidgetItem(f"{entry.name} — Sharpe {entry.sharpe}")
            item.setData(Qt.ItemDataRole.UserRole, entry.experiment_id)
            self._list.addItem(item)
        if self._entries:
            self._list.setCurrentRow(0)
        self._calendar.set_entries(self._entries)

    def _on_calendar_day(self, day_key: str) -> None:
        for i, entry in enumerate(self._entries):
            if entry.run_at.startswith(day_key):
                self._tabs.setCurrentIndex(0)
                self._list.setCurrentRow(i)
                return

    def _on_row_changed(self, row: int) -> None:
        if row < 0 or row >= len(self._entries):
            self._selected_id = None
            self._detail.clear()
            return
        entry = self._entries[row]
        self._selected_id = entry.experiment_id
        self._detail.setPlainText(entry.note)
        self._saved.setText(entry.summary)

    def _save_note(self) -> None:
        if not self._selected_id:
            return
        if self._assistant.save_journal_note(self._selected_id, self._detail.toPlainText()):
            self._saved.setText("Saved.")
            self.refresh()
