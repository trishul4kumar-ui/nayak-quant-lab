"""Native status surface for the persisted daily research desk."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFormLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from quantlab.agent_desk.models import DailyDeskState


class DailyDeskWorkspace(QWidget):
    pauseRequested = Signal()

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        self.summary = QLabel("No persisted daily desk state · research scheduler is inactive")
        self.summary.setWordWrap(True)
        layout.addWidget(self.summary)
        fields = QFormLayout()
        self.phase = QLabel("—")
        self.session = QLabel("—")
        self.calendar = QLabel("—")
        self.health = QLabel("—")
        for label, value in (
            ("Daily phase", self.phase),
            ("Market session", self.session),
            ("Calendar", self.calendar),
            ("Research state", self.health),
        ):
            fields.addRow(label, value)
        layout.addLayout(fields)
        self.pause = QPushButton("Pause AI research")
        self.pause.clicked.connect(self.pauseRequested)
        layout.addWidget(self.pause)
        self.resume = QPushButton("Resume AI research")
        self.resume.setEnabled(False)
        self.resume.setToolTip("Requires an active sourced exchange-calendar provider.")
        layout.addWidget(self.resume)
        layout.addStretch(1)

    def set_state(self, state: DailyDeskState | None) -> None:
        if state is None:
            self.phase.setText("—")
            self.session.setText("—")
            self.calendar.setText("—")
            self.health.setText("No daily desk state")
            self.pause.setEnabled(False)
            return
        self.phase.setText(state.phase.value)
        self.session.setText(state.session.value)
        self.calendar.setText(f"{state.calendar_version} · {state.calendar_provenance}")
        self.health.setText("Paused" if state.paused else "Bounded research-only scheduler")
        self.summary.setText(
            "Daily desk is persisted and research-only. No auto-trade or live-order control exists."
        )
        self.pause.setEnabled(not state.paused)
