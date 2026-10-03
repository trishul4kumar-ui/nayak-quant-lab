"""Shared lab page chrome — title, NAYAK voice, empty states, tips."""

from __future__ import annotations

from collections.abc import Callable
from contextlib import suppress

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSplitter,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from quantlab.app.settings_store import UiDensity, UiSettingsStore


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
        self.setObjectName("labShell")
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
        self._interaction_status = QLabel("READY")
        self._interaction_status.setObjectName("pageActionStatus")
        self._interaction_status.setToolTip("The most recent action received by this workspace")
        self._interaction_status.setFixedHeight(28)
        self._interaction_status.setMaximumWidth(220)
        self._interaction_status.setStyleSheet(
            "background: #173327; color: #4bd0a7; border: 1px solid #275343; "
            "border-radius: 4px; padding: 4px 8px; font-size: 10px; font-weight: 700;"
        )
        header.addWidget(
            self._interaction_status,
            alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight,
        )
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
        self._workspace_splitter: QSplitter | None = None
        self._workspace_layout_id: str | None = None
        self._workspace_settings: UiSettingsStore | None = None
        self._layout_reset: QPushButton | None = None
        self._interaction_timer = QTimer(self)
        self._interaction_timer.setSingleShot(True)
        self._interaction_timer.timeout.connect(self._restore_ready_status)
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

    def show_interaction_feedback(self, message: str) -> None:
        """Expose input acknowledgement inside the active workspace, not only the footer."""
        self._interaction_timer.stop()
        action = message.removeprefix("Action received:").strip()
        self._interaction_status.setText(f"ACK · {action.upper()}")
        self._interaction_status.setToolTip(message)
        self._interaction_status.setStyleSheet(
            "background: #12344a; color: #66c8f2; border: 1px solid #286581; "
            "border-radius: 4px; padding: 4px 8px; font-size: 10px; font-weight: 700;"
        )
        self._interaction_timer.start(2600)

    def _restore_ready_status(self) -> None:
        self._interaction_status.setText("READY")
        self._interaction_status.setToolTip("The workspace is ready for the next action")
        self._interaction_status.setStyleSheet(
            "background: #173327; color: #4bd0a7; border: 1px solid #275343; "
            "border-radius: 4px; padding: 4px 8px; font-size: 10px; font-weight: 700;"
        )

    def enable_terminal_layout(self, *, layout_id: str, settings: UiSettingsStore) -> None:
        """Turn the completed page body into a persisted, vertically resizable workspace.

        Pages continue to build with the familiar ``body()`` layout during construction.
        The main window calls this after every page is complete, so the behaviour is
        consistent without forcing each lab to hand-code splitter plumbing.
        """
        if self._workspace_splitter is not None:
            return
        self._workspace_layout_id = layout_id
        self._workspace_settings = settings
        sections: list[tuple[QWidget, int]] = []
        while self._body.count() > 1:
            item = self._body.takeAt(1)
            if item is None:
                break
            widget = item.widget()
            item_layout = item.layout()
            if widget is None and item_layout is not None:
                widget = QWidget()
                widget.setLayout(item_layout)
            if widget is not None:
                sections.append((widget, max(item.maximumSize().height(), 1)))
        if len(sections) < 2:
            self._restore_workspace_layout()
            return

        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setObjectName("workspaceSplitter")
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(8)
        splitter.setOpaqueResize(True)
        for widget, _stretch in sections:
            splitter.addWidget(widget)
            widget.setMinimumHeight(max(widget.minimumSizeHint().height(), 44))
        for index in range(1, splitter.count()):
            splitter.handle(index).setToolTip("Drag to resize workspace panels")
        splitter.splitterMoved.connect(self._persist_workspace_layout)
        self._body.addWidget(splitter, 1)

        self._workspace_splitter = splitter
        self._restore_workspace_layout()
        self._add_layout_reset()

    def register_splitter(self, splitter: QSplitter, name: str) -> None:
        """Persist an additional page-local splitter, such as the journal detail pane."""
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(8)
        splitter.setOpaqueResize(True)
        for index in range(1, splitter.count()):
            splitter.handle(index).setToolTip("Drag to resize panels")
        splitter.setProperty("terminal_layout_name", name)
        splitter.splitterMoved.connect(self._persist_workspace_layout)
        self._add_layout_reset()

    def _add_layout_reset(self) -> None:
        if self._layout_reset is not None:
            return
        self._layout_reset = QPushButton("Reset panels")
        self._layout_reset.setToolTip("Restore the default panel heights for this page")
        self._layout_reset.clicked.connect(self.reset_terminal_layout)
        self.add_toolbar_widget(self._layout_reset)

    def reset_terminal_layout(self) -> None:
        if self._workspace_splitter is not None:
            self._workspace_splitter.setSizes([100] * self._workspace_splitter.count())
        for splitter in self.findChildren(QSplitter):
            if splitter is self._workspace_splitter:
                continue
            splitter.setSizes([100] * splitter.count())
        for widget in self.findChildren(QWidget):
            reset = getattr(widget, "reset_layout", None)
            if callable(reset):
                reset()
        self._persist_workspace_layout()

    def has_terminal_layout(self) -> bool:
        return self._workspace_splitter is not None or bool(self.findChildren(QSplitter))

    def _persist_workspace_layout(self, *_args: object) -> None:
        if self._workspace_settings is None or self._workspace_layout_id is None:
            return
        payload: dict[str, list[int]] = {}
        if self._workspace_splitter is not None:
            payload["main"] = self._workspace_splitter.sizes()
        for splitter in self.findChildren(QSplitter):
            name = splitter.property("terminal_layout_name")
            if isinstance(name, str) and name:
                payload[name] = splitter.sizes()
        self._workspace_settings.current.terminal_layouts[self._workspace_layout_id] = payload
        self._workspace_settings.save()

    def _restore_workspace_layout(self) -> None:
        if self._workspace_settings is None or self._workspace_layout_id is None:
            return
        layouts = self._workspace_settings.current.terminal_layouts
        payload = layouts.get(self._workspace_layout_id, {})
        if self._workspace_splitter is not None:
            sizes = payload.get("main")
            if sizes and len(sizes) == self._workspace_splitter.count():
                self._workspace_splitter.setSizes(sizes)
        for splitter in self.findChildren(QSplitter):
            name = splitter.property("terminal_layout_name")
            if not isinstance(name, str) or not name:
                continue
            sizes = payload.get(name)
            if sizes and len(sizes) == splitter.count():
                splitter.setSizes(sizes)
