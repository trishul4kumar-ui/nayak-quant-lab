from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
)

from quantlab.app.ai_chat import ai_status, chat
from quantlab.app.assistant import NayakAssistant
from quantlab.app.bootstrap import ApplicationRuntime
from quantlab.ui.widgets.lab_shell import LabPageShell


class AiResearchPage(LabPageShell):
    def __init__(self, runtime: ApplicationRuntime) -> None:
        super().__init__(
            "AI Research",
            subtitle="Ask NAYAK about metrics, workflow, and ideas — not live orders.",
            nayak_summary=(
                "I can explain Sharpe, momentum, validation, and lab workflow. "
                "I cannot place live orders or override the research gate."
            ),
        )
        self._runtime = runtime
        self._assistant = NayakAssistant(runtime)

        self._status = QLabel()
        self.add_toolbar_widget(self._status)

        self._scroll = QScrollArea()
        self._scroll.setObjectName("pageScroll")
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self._transcript_host = QFrame()
        self._transcript = QVBoxLayout(self._transcript_host)
        self._transcript.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._scroll.setWidget(self._transcript_host)
        self.body().addWidget(self._scroll, 1)

        input_row = QHBoxLayout()
        self._input = QLineEdit()
        self._input.setPlaceholderText("Ask about Sharpe, momentum, validation…")
        self._input.returnPressed.connect(self._send)
        self._send_button = QPushButton("Send")
        self._send_button.setObjectName("primary")
        self._send_button.setEnabled(False)
        self._send_button.setToolTip("Type a question first")
        self._send_button.clicked.connect(self._send)
        self._input.textChanged.connect(self._sync_send_enabled)
        input_row.addWidget(self._input, 1)
        input_row.addWidget(self._send_button)
        self.body().addLayout(input_row)
        self.refresh()

    def refresh(self) -> None:
        status = ai_status()
        mode = "LLM connected" if status.connected else "Local NAYAK"
        self._status.setText(f"{mode} · {status.detail}")

    def _send(self) -> None:
        text = self._input.text().strip()
        if not text:
            return
        self._input.clear()
        self._append_message("TK", text, user=True)
        reply = chat(self._runtime, text)
        self._append_message("NAYAK", reply, user=False)

    def _sync_send_enabled(self, text: str) -> None:
        self._send_button.setEnabled(bool(text.strip()))

    def _append_message(self, speaker: str, body: str, *, user: bool) -> None:
        frame = QFrame()
        frame.setObjectName("chatUser" if user else "chatNayak")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 10, 12, 10)
        who = QLabel(speaker)
        who.setStyleSheet("font-weight: 600; font-size: 11px;")
        text = QLabel(body)
        text.setWordWrap(True)
        layout.addWidget(who)
        layout.addWidget(text)
        self._transcript.addWidget(frame)
        self._scroll.verticalScrollBar().setValue(self._scroll.verticalScrollBar().maximum())
