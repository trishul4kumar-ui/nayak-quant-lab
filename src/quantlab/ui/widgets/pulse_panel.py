"""Home Pulse panel — color-coded, clickable operational status."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from quantlab.app.bootstrap import ApplicationRuntime
from quantlab.app.pulse import PulseItem, build_pulse_items

_TONES = {
    "ok": ("#1a2e28", "#26a69a", "#42a5f5"),
    "warn": ("#2e2a1a", "#ffb74d", "#ffb74d"),
    "bad": ("#2e1a1a", "#ef5350", "#ef5350"),
    "neutral": ("#252932", "#9aa1ad", "#b4b8c2"),
}


class PulseCard(QFrame):
    clicked = Signal(str)

    def __init__(self, item: PulseItem) -> None:
        super().__init__()
        self._nav_key = item.nav_key
        self.setObjectName("pulseCardItem")
        bg, accent, value_color = _TONES.get(item.tone, _TONES["neutral"])
        self.setStyleSheet(
            f"QFrame#pulseCardItem {{ background: {bg}; border: none; border-radius: 6px; }}"
            f"QFrame#pulseCardItem:hover {{ background: {bg}; }}"
        )
        if item.nav_key:
            self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(2)

        top = QHBoxLayout()
        dot = QLabel("●")
        dot.setStyleSheet(f"color: {accent}; font-size: 8px;")
        title = QLabel(item.title)
        title.setStyleSheet("color: #9aa1ad; font-size: 11px;")
        top.addWidget(dot)
        top.addWidget(title)
        top.addStretch()
        layout.addLayout(top)

        value = QLabel(item.value)
        value.setStyleSheet(f"font-size: 15px; font-weight: 700; color: {value_color};")
        layout.addWidget(value)

        detail = QLabel(item.detail)
        detail.setWordWrap(True)
        detail.setStyleSheet("color: #6b7080; font-size: 10px;")
        layout.addWidget(detail)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if self._nav_key:
            self.clicked.emit(self._nav_key)
        super().mousePressEvent(event)


class PulsePanel(QFrame):
    """Operational status grid for the Home page."""

    navigate = Signal(str)

    def __init__(self, on_nav: Callable[[str], None] | None = None) -> None:
        super().__init__()
        self.setObjectName("pulseCard")
        self._on_nav = on_nav

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(10)

        header = QHBoxLayout()
        title = QLabel("Pulse")
        title.setStyleSheet("font-weight: 600; font-size: 14px;")
        self._summary = QLabel()
        self._summary.setObjectName("pulseSummary")
        self._summary.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        header.addWidget(title)
        header.addWidget(self._summary, 1)
        root.addLayout(header)

        self._grid_host = QWidget()
        self._grid = QGridLayout(self._grid_host)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setSpacing(8)
        root.addWidget(self._grid_host)

        footer = QHBoxLayout()
        self._open_system = QPushButton("Open System →")
        self._open_system.setFlat(True)
        self._open_system.setStyleSheet("color: #6ba3b8; font-size: 12px; text-align: left;")
        self._open_system.clicked.connect(lambda: self._emit_nav("system"))
        footer.addWidget(self._open_system)
        footer.addStretch()
        root.addLayout(footer)

    def _emit_nav(self, key: str) -> None:
        self.navigate.emit(key)
        if self._on_nav is not None:
            self._on_nav(key)

    def refresh(self, runtime: ApplicationRuntime) -> None:
        summary, items, summary_tone = build_pulse_items(runtime)
        bg, accent, _ = _TONES.get(summary_tone, _TONES["neutral"])
        self._summary.setText(summary)
        self._summary.setStyleSheet(
            f"background: {bg}; color: {accent}; padding: 4px 10px; "
            "border-radius: 4px; font-size: 11px; font-weight: 600;"
        )

        while self._grid.count():
            taken = self._grid.takeAt(0)
            if taken is None:
                break
            widget = taken.widget()
            if widget is not None:
                widget.deleteLater()

        for i, item in enumerate(items):
            card = PulseCard(item)
            card.clicked.connect(self._emit_nav)
            self._grid.addWidget(card, i // 2, i % 2)
