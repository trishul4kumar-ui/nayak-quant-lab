"""Horizontal research pipeline strip for Home."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from quantlab.app.bootstrap import ApplicationRuntime
from quantlab.app.research_pipeline import PipelineStage, PipelineStatus, build_research_pipeline

_STATUS_STYLE = {
    PipelineStatus.PENDING: ("#252932", "#6b7080", "○"),
    PipelineStatus.RUNNING: ("#1a2433", "#42a5f5", "●"),
    PipelineStatus.PASS: ("#1a2e28", "#26a69a", "✓"),
    PipelineStatus.FAIL: ("#2e1a1a", "#ef5350", "✗"),
    PipelineStatus.BLOCKED: ("#2e2a1a", "#ffb74d", "🔒"),
}


class _StageChip(QFrame):
    clicked = Signal(str)

    def __init__(self, stage: PipelineStage) -> None:
        super().__init__()
        self._nav_key = stage.nav_key
        bg, fg, icon = _STATUS_STYLE.get(stage.status, _STATUS_STYLE[PipelineStatus.PENDING])
        self.setObjectName("pipelineStage")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(
            f"QFrame#pipelineStage {{ background: {bg}; border: none; border-radius: 6px; }}"
            f"QFrame#pipelineStage:hover {{ border: 1px solid {fg}; }}"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(2)
        top = QHBoxLayout()
        mark = QLabel(icon)
        mark.setStyleSheet(f"color: {fg}; font-size: 11px;")
        title = QLabel(stage.label)
        title.setStyleSheet(f"color: {fg}; font-weight: 600; font-size: 12px;")
        top.addWidget(mark)
        top.addWidget(title)
        top.addStretch()
        detail = QLabel(stage.detail)
        detail.setStyleSheet("color: #9aa1ad; font-size: 10px;")
        layout.addLayout(top)
        layout.addWidget(detail)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        self.clicked.emit(self._nav_key)
        super().mousePressEvent(event)


class ResearchPipelineStrip(QWidget):
    """Idea → Backtest → Validate → Journal → Live."""

    def __init__(self, *, on_nav: Callable[[str], None] | None = None) -> None:
        super().__init__()
        self._on_nav = on_nav
        self._host = QHBoxLayout(self)
        self._host.setContentsMargins(0, 0, 0, 0)
        self._host.setSpacing(6)
        self._stages: list[PipelineStage] = []

    def refresh(self, runtime: ApplicationRuntime) -> None:
        self._stages = build_research_pipeline(runtime)
        while self._host.count():
            item = self._host.takeAt(0)
            if item is None:
                break
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        for i, stage in enumerate(self._stages):
            chip = _StageChip(stage)
            if self._on_nav is not None:
                chip.clicked.connect(self._on_nav)
            self._host.addWidget(chip, 1)
            if i < len(self._stages) - 1:
                arrow = QLabel("→")
                arrow.setStyleSheet("color: #6b7080; font-size: 14px;")
                self._host.addWidget(arrow)
