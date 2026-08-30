"""Stronger LIVE mode confirmation — checklist + explicit acknowledgment."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QLabel,
    QVBoxLayout,
)

from quantlab.app.live_ops import live_gate_rows
from quantlab.app.bootstrap import ApplicationRuntime
from quantlab.ui.widgets.lab_shell import StatusBadge


class LiveConfirmDialog(QDialog):
    def __init__(self, runtime: ApplicationRuntime, *, parent=None) -> None:
        super().__init__(parent)
        self._runtime = runtime
        self.setWindowTitle("Enable live trading")
        self.setMinimumWidth(480)
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        banner = QLabel("LIVE TRADING REQUEST")
        banner.setObjectName("liveBanner")
        banner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(banner)

        warn = QLabel(
            "Orders may result in real financial losses. "
            "The UI cannot bypass the risk firewall — every gate below must pass."
        )
        warn.setWordWrap(True)
        warn.setObjectName("nayakVoice")
        layout.addWidget(warn)

        status = runtime.status
        layout.addWidget(StatusBadge("warn", text=f"Broker: {status.broker}"))
        layout.addWidget(StatusBadge("warn", text=f"Risk: {runtime.risk_state.value}"))

        gate_frame = QFrame()
        gate_frame.setObjectName("card")
        gate_layout = QVBoxLayout(gate_frame)
        gate_layout.setContentsMargins(14, 12, 14, 12)
        gate_head = QLabel("Safety gate checklist")
        gate_head.setStyleSheet("font-weight: 600;")
        gate_layout.addWidget(gate_head)
        self._gate_lines: list[tuple[str, bool]] = live_gate_rows(runtime.gates)
        for label, ok in self._gate_lines:
            mark = "✓" if ok else "✗"
            line = QLabel(f"{mark}  {label}")
            line.setObjectName("nayakVoice")
            if not ok:
                line.setStyleSheet("color: #ef5350;")
            gate_layout.addWidget(line)
        layout.addWidget(gate_frame)

        self._ack = QCheckBox("I understand live orders may cause real financial losses.")
        layout.addWidget(self._ack)

        self._buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok
        )
        self._buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Request live trading")
        self._buttons.accepted.connect(self.accept)
        self._buttons.rejected.connect(self.reject)
        layout.addWidget(self._buttons)
        self._refresh_buttons()

        self._ack.stateChanged.connect(lambda _: self._refresh_buttons())

    def _refresh_buttons(self) -> None:
        ok_btn = self._buttons.button(QDialogButtonBox.StandardButton.Ok)
        all_gates = all(met for _, met in self._gate_lines)
        ok_btn.setEnabled(self._ack.isChecked() and all_gates)
        if not all_gates:
            ok_btn.setToolTip("All safety gates must pass before live trading can be requested.")
        elif not self._ack.isChecked():
            ok_btn.setToolTip("Check the acknowledgment box to continue.")
        else:
            ok_btn.setToolTip("")
