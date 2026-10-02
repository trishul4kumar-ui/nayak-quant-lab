"""Shared lab page chrome — title, NAYAK voice, empty states, tips."""

from __future__ import annotations

from collections.abc import Callable
from contextlib import suppress

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from quantlab.app.settings_store import UiDensity


class StatusBadge(QLabel):
    """Small semantic status pill for tables and headers."""

    _STYLES = {
        "pass": ("PASS", "#1a2e28", "#26a69a"),
        "warn": ("WARN", "#2e2a1a", "#ffb74d"),
        "fail": ("FAIL", "#2e1a1a", "#ef5350"),
        "synthetic": ("SYNTHETIC", "#2a2620", "#c9a96e"),
        "blocked": ("BLOCKED", "#2e1a1a", "#ef5350"),
        "ready": ("READY", "#1a2e28", "#26a69a"),
        "ok": ("OK", "#1a2e28", "#26a69a"),
        "off": ("OFF", "#252932", "#9aa1ad"),
    }

    def __init__(self, kind: str, *, text: str | None = None) -> None:
        super().__init__()
        label, bg, fg = self._STYLES.get(kind, (kind.upper(), "#252932", "#b4b8c2"))
        self.setText(text or label)
        self.setObjectName("statusBadge")
        self.setStyleSheet(
            f"background: {bg}; color: {fg}; padding: 2px 8px; "
            "border-radius: 4px; font-size: 11px; font-weight: 600;"
        )


def badge_for_value(value: str) -> StatusBadge | None:
    lowered = value.strip().lower()
    if lowered in {"pass", "passed", "ok", "true", "ready", "healthy"}:
        return StatusBadge("pass", text=value if value.lower() not in {"pass", "ok"} else None)
    if lowered in {"warn", "warning", "slice"}:
        return StatusBadge("warn", text=value.upper() if len(value) <= 8 else "WARN")
    if lowered in {"fail", "failed", "false", "blocked", "disabled", "disconnected"}:
        return StatusBadge("fail", text=value.upper() if len(value) <= 12 else "FAIL")
    if lowered == "synthetic":
        return StatusBadge("synthetic")
    return None


def data_kind_badge(data_kind: str | None) -> StatusBadge:
    """Consistent SYNTHETIC / REAL pill for experiment result surfaces."""
    kind = (data_kind or "synthetic").strip().lower()
    if kind == "synthetic":
        return StatusBadge("synthetic")
    if kind in {"real", "live", "nse"}:
        return StatusBadge("ready", text=kind.upper())
    return StatusBadge("warn", text=kind.upper()[:12])


class RunningBanner(QFrame):
    """Inline job progress indicator for backtest / validation pages."""

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("runningBanner")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        self._label = QLabel()
        self._label.setObjectName("nayakVoice")
        layout.addWidget(self._label)
        self.setVisible(False)

    def set_message(self, message: str | None) -> None:
        if message:
            self._label.setText(message)
            self.setVisible(True)
        else:
            self.setVisible(False)


class EmptyState(QFrame):
    def __init__(
        self,
        title: str,
        body: str,
        *,
        action_label: str | None = None,
        on_action: Callable[[], None] | None = None,
    ) -> None:
        super().__init__()
        self.setObjectName("emptyState")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        head = QLabel(title)
        head.setStyleSheet("font-size: 16px; font-weight: 600;")
        head.setAlignment(Qt.AlignmentFlag.AlignCenter)
        text = QLabel(body)
        text.setWordWrap(True)
        text.setObjectName("nayakVoice")
        text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(head)
        layout.addWidget(text)
        self._action_btn: QPushButton | None = None
        if action_label and on_action is not None:
            self._action_btn = QPushButton(action_label)
            self._action_btn.setObjectName("primary")
            self._action_btn.clicked.connect(on_action)
            layout.addWidget(self._action_btn, alignment=Qt.AlignmentFlag.AlignCenter)

    def set_action(self, action_label: str | None, on_action: Callable[[], None] | None) -> None:
        if self._action_btn is None:
            return
        visible = bool(action_label and on_action is not None)
        self._action_btn.setVisible(visible)
        if action_label:
            self._action_btn.setText(action_label)
        if on_action is not None:
            with suppress(RuntimeError):
                self._action_btn.clicked.disconnect()
            self._action_btn.clicked.connect(on_action)


class NayakTip(QFrame):
    """Plain-language summary with optional collapsible technical note."""

    def __init__(self, summary: str, *, technical: str = "") -> None:
        super().__init__()
        self.setObjectName("nayakTip")
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 10)
        self._summary = QLabel(summary)
        self._summary.setWordWrap(True)
        self._summary.setObjectName("nayakVoice")
        root.addWidget(self._summary)
        self._tech_btn: QToolButton | None = None
        self._tech_label: QLabel | None = None
        if technical:
            self._tech_btn = QToolButton()
            self._tech_btn.setText("Technical details ▸")
            self._tech_btn.setStyleSheet("border: none; color: #6ba3b8;")
            self._tech_btn.clicked.connect(self._toggle_technical)
            self._tech_label = QLabel(technical)
            self._tech_label.setWordWrap(True)
            self._tech_label.setVisible(False)
            self._tech_label.setStyleSheet("color: #6b7080; font-size: 12px;")
            root.addWidget(self._tech_btn)
            root.addWidget(self._tech_label)

    def _toggle_technical(self) -> None:
        if self._tech_label is None or self._tech_btn is None:
            return
        visible = not self._tech_label.isVisible()
        self._tech_label.setVisible(visible)
        self._tech_btn.setText("Technical details ▾" if visible else "Technical details ▸")


class LabPageShell(QWidget):
    """Standard page frame: title, subtitle, optional tip, toolbar slot, body."""

    def __init__(
        self,
        title: str,
        *,
        subtitle: str = "",
        nayak_summary: str = "",
        technical: str = "",
    ) -> None:
        super().__init__()
        outer = QVBoxLayout(self)
        self._outer = outer

        header = QHBoxLayout()
        title_col = QVBoxLayout()
        self._title = QLabel(title)
        self._title.setObjectName("pageTitle")
        self._title.setStyleSheet("font-size: 20px; font-weight: 600;")
        title_col.addWidget(self._title)
        if subtitle:
            sub = QLabel(subtitle)
            sub.setObjectName("pageSubtitle")
            sub.setWordWrap(True)
            sub.setStyleSheet("color: #9aa1ad; font-size: 13px;")
            title_col.addWidget(sub)
        header.addLayout(title_col, 1)
        self._toolbar = QHBoxLayout()
        header.addLayout(self._toolbar)
        outer.addLayout(header)

        if nayak_summary:
            outer.addWidget(NayakTip(nayak_summary, technical=technical))

        self._body = QVBoxLayout()
        self._body.setSpacing(12)
        outer.addLayout(self._body, 1)

        self._running = RunningBanner()
        self._body.addWidget(self._running)
        self._apply_density(UiDensity.COMFORTABLE)

    def apply_density(self, density: UiDensity) -> None:
        self._apply_density(density)

    def _apply_density(self, density: UiDensity) -> None:
        margin = 8 if density is UiDensity.COMPACT else 16
        spacing = 8 if density is UiDensity.COMPACT else 12
        self._outer.setContentsMargins(margin, margin, margin, margin)
        self._outer.setSpacing(spacing)
        self._body.setSpacing(spacing)

    def set_running(self, message: str | None) -> None:
        self._running.set_message(message)

    def body(self) -> QVBoxLayout:
        return self._body

    def add_toolbar_widget(self, widget: QWidget) -> None:
        self._toolbar.addWidget(widget)
