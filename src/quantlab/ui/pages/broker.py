from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from quantlab.app.bootstrap import ApplicationRuntime
from quantlab.app.live_ops import live_gate_rows
from quantlab.ui.widgets.lab_shell import LabPageShell, StatusBadge


class BrokerPage(LabPageShell):
    """Connection wizard — stub adapters only; credentials never touch the UI."""

    def __init__(self, runtime: ApplicationRuntime) -> None:
        super().__init__(
            "Broker Console",
            subtitle="Configure connectivity for paper or live — research mode stays closed by default.",
            nayak_summary=(
                "This wizard walks through adapter choice and safety gates. "
                "API keys and passwords are never stored or displayed here. "
                "Completing paper setup does not enable live orders."
            ),
        )
        self._runtime = runtime
        self._step = 0

        self._step_label = QLabel("Step 1 of 3")
        self._step_label.setStyleSheet("color: #6b7080;")
        self.add_toolbar_widget(self._step_label)

        self._status_badge = StatusBadge("blocked", text="DISCONNECTED")
        self.add_toolbar_widget(self._status_badge)

        body = self.body()
        self._stack = QStackedWidget()
        self._stack.addWidget(self._build_adapter_step())
        self._stack.addWidget(self._build_safety_step())
        self._stack.addWidget(self._build_connect_step())
        body.addWidget(self._stack, 1)

        nav = QHBoxLayout()
        self._back = QPushButton("Back")
        self._back.clicked.connect(self._go_back)
        self._next = QPushButton("Next")
        self._next.setObjectName("primary")
        self._next.clicked.connect(self._go_next)
        nav.addWidget(self._back)
        nav.addStretch()
        nav.addWidget(self._next)
        body.addLayout(nav)
        self.refresh()

    def _build_adapter_step(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        head = QLabel("Choose an adapter")
        head.setStyleSheet("font-weight: 600;")
        layout.addWidget(head)
        hint = QLabel(
            "Paper is recommended while you learn the lab. "
            "Zerodha and OpenAlgo remain stubbed until Prompt 18 OMS lands."
        )
        hint.setWordWrap(True)
        hint.setObjectName("nayakVoice")
        layout.addWidget(hint)

        self._adapter_group = QButtonGroup(self)
        for idx, (adapter_id, title, detail) in enumerate(
            (
                ("paper", "Paper (recommended)", "Simulated connectivity — no real orders."),
                ("zerodha", "Zerodha Kite", "Stub — requires env credentials outside the UI."),
                ("openalgo", "OpenAlgo", "Stub — local bridge not wired in this build."),
            )
        ):
            radio = QRadioButton(title)
            radio.setProperty("adapter_id", adapter_id)
            self._adapter_group.addButton(radio, idx)
            layout.addWidget(radio)
            sub = QLabel(detail)
            sub.setObjectName("nayakVoice")
            sub.setStyleSheet("margin-left: 24px; margin-bottom: 8px;")
            layout.addWidget(sub)
        self._adapter_group.button(0).setChecked(True)
        layout.addStretch()
        return page

    def _build_safety_step(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        head = QLabel("Safety checklist")
        head.setStyleSheet("font-weight: 600;")
        layout.addWidget(head)
        self._gate_host = QVBoxLayout()
        layout.addLayout(self._gate_host)
        self._no_secrets = QCheckBox(
            "I understand broker secrets are configured outside the UI (env / keychain)."
        )
        self._no_secrets.stateChanged.connect(lambda _: self._update_nav())
        layout.addWidget(self._no_secrets)
        layout.addStretch()
        return page

    def _build_connect_step(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        self._connect_title = QLabel()
        self._connect_title.setStyleSheet("font-weight: 600;")
        self._connect_body = QLabel()
        self._connect_body.setWordWrap(True)
        self._connect_body.setObjectName("nayakVoice")
        layout.addWidget(self._connect_title)
        layout.addWidget(self._connect_body)
        layout.addStretch()
        return page

    def _selected_adapter(self) -> str:
        btn = self._adapter_group.checkedButton()
        if btn is None:
            return "paper"
        return str(btn.property("adapter_id") or "paper")

    def _paint_gates(self) -> None:
        while self._gate_host.count():
            item = self._gate_host.takeAt(0)
            if item is None:
                break
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        for label, ok in live_gate_rows(self._runtime.gates):
            mark = "✓" if ok else "✗"
            line = QLabel(f"{mark}  {label}")
            line.setObjectName("nayakVoice")
            if not ok:
                line.setStyleSheet("color: #ef5350;")
            self._gate_host.addWidget(line)

    def _go_back(self) -> None:
        if self._step > 0:
            self._step -= 1
            self._stack.setCurrentIndex(self._step)
            self._update_nav()

    def _go_next(self) -> None:
        if self._step == 0:
            self._step = 1
            self._stack.setCurrentIndex(1)
            self._paint_gates()
            self._update_nav()
            return
        if self._step == 1:
            if not self._no_secrets.isChecked():
                return
            self._step = 2
            self._stack.setCurrentIndex(2)
            self._finish_setup()
            self._update_nav()
            return
        self.refresh()

    def _finish_setup(self) -> None:
        prefs = self._runtime.ui_settings.current
        adapter = self._selected_adapter()
        prefs.broker_adapter = adapter
        prefs.broker_wizard_complete = True
        self._runtime.ui_settings.save()
        if adapter == "paper":
            self._connect_title.setText("Paper adapter configured")
            self._connect_body.setText(
                "Connectivity flow complete for paper mode. "
                "Orders still do not leave the lab — use Portfolio Lab to inspect demo targets."
            )
        else:
            self._connect_title.setText(f"{adapter.title()} adapter selected (stub)")
            self._connect_body.setText(
                "Adapter preference saved. Real connection requires env configuration "
                "and every live safety gate — the UI cannot connect on its own."
            )

    def _update_nav(self) -> None:
        self._step_label.setText(f"Step {self._step + 1} of 3")
        self._back.setEnabled(self._step > 0)
        if self._step == 0:
            self._next.setText("Next →")
            self._next.setEnabled(True)
        elif self._step == 1:
            self._next.setText("Acknowledge & continue →")
            self._next.setEnabled(self._no_secrets.isChecked())
        else:
            self._next.setText("Done")
            self._next.setEnabled(True)

    def refresh(self) -> None:
        prefs = self._runtime.ui_settings.current
        gates = self._runtime.gates
        if gates.broker_connected:
            self._status_badge.setText("CONNECTED")
            self._status_badge.setStyleSheet(
                "background: #1a2e28; color: #26a69a; padding: 2px 8px; "
                "border-radius: 4px; font-size: 11px; font-weight: 600;"
            )
        elif prefs.broker_wizard_complete:
            self._status_badge.setText(f"{prefs.broker_adapter.upper()} READY")
            self._status_badge.setStyleSheet(
                "background: #2e2a1a; color: #ffb74d; padding: 2px 8px; "
                "border-radius: 4px; font-size: 11px; font-weight: 600;"
            )
        else:
            self._status_badge.setText("DISCONNECTED")
        if prefs.broker_adapter:
            for btn in self._adapter_group.buttons():
                if btn.property("adapter_id") == prefs.broker_adapter:
                    btn.setChecked(True)
                    break
        self._paint_gates()
        self._update_nav()
