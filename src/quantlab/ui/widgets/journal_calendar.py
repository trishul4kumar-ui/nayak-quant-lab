"""Month calendar heatmap for journal run dates."""

from __future__ import annotations

from calendar import monthcalendar
from datetime import UTC, datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QFrame, QGridLayout, QLabel, QVBoxLayout, QWidget

from quantlab.app.assistant import JournalEntry


class JournalCalendarWidget(QFrame):
    day_selected = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        self._title = QLabel()
        self._title.setStyleSheet("font-weight: 600;")
        self._grid_host = QWidget()
        self._grid = QGridLayout(self._grid_host)
        self._grid.setSpacing(4)
        self._entries: list[JournalEntry] = []
        self._by_day: dict[str, list[JournalEntry]] = {}
        layout.addWidget(self._title)
        layout.addWidget(self._grid_host)

    def set_entries(self, entries: list[JournalEntry]) -> None:
        self._entries = list(entries)
        self._by_day.clear()
        for entry in entries:
            run_day = entry.run_at[:10] if entry.run_at and len(entry.run_at) >= 10 else ""
            if not run_day:
                continue
            self._by_day.setdefault(run_day, []).append(entry)
        now = datetime.now(tz=UTC)
        self._title.setText(now.strftime("%B %Y"))
        while self._grid.count():
            item = self._grid.takeAt(0)
            if item is None:
                break
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        for col, head in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]):
            lbl = QLabel(head)
            lbl.setStyleSheet("color: #6b7080; font-size: 10px;")
            self._grid.addWidget(lbl, 0, col)
        year, month = now.year, now.month
        for row_idx, week in enumerate(monthcalendar(year, month), start=1):
            for col_idx, calendar_day in enumerate(week):
                if calendar_day == 0:
                    spacer = QLabel("")
                    self._grid.addWidget(spacer, row_idx, col_idx)
                    continue
                key = f"{year:04d}-{month:02d}-{calendar_day:02d}"
                cell = _DayCell(calendar_day, self._by_day.get(key, []))
                cell.clicked.connect(self.day_selected.emit)
                self._grid.addWidget(cell, row_idx, col_idx)


class _DayCell(QFrame):
    clicked = Signal(str)

    def __init__(self, day: int, entries: list[JournalEntry]) -> None:
        super().__init__()
        self._day_key = ""
        self.setObjectName("journalDay")
        if entries:
            self._day_key = entries[0].run_at[:10]
            bg = "#1a2e28" if any("pass" in e.summary.lower() for e in entries) else "#252932"
            accent = "#26a69a"
        else:
            bg = "#252932"
            accent = "#6b7080"
        self.setStyleSheet(
            f"QFrame#journalDay {{ background: {bg}; border: none; "
            "border-radius: 4px; min-height: 36px; }"
        )
        if entries:
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        num = QLabel(str(day))
        num.setStyleSheet(f"color: {accent}; font-size: 11px; font-weight: 600;")
        layout.addWidget(num)
        if entries:
            sub = QLabel(f"{len(entries)} run(s)")
            sub.setStyleSheet("color: #9aa1ad; font-size: 9px;")
            layout.addWidget(sub)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if self._day_key:
            self.clicked.emit(self._day_key)
        super().mousePressEvent(event)
