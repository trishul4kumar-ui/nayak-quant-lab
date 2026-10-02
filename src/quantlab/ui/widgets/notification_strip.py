"""Transient lab notifications — backtest done, validation done, etc."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QWidget


class NotificationStrip(QFrame):
    def __init__(
        self,
        *,
        on_dismiss: Callable[[], None] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._on_dismiss = on_dismiss
        self.setObjectName("nayakTip")
        self.setVisible(False)
        row = QHBoxLayout(self)
        row.setContentsMargins(10, 8, 10, 8)
        self._icon = QLabel("●")
        self._icon.setStyleSheet("color: #42a5f5; font-size: 10px;")
        self._text = QLabel()
        self._text.setWordWrap(True)
        self._text.setObjectName("nayakVoice")
        dismiss = QPushButton("Dismiss")
        dismiss.setFlat(True)
        dismiss.clicked.connect(self._dismiss)
        row.addWidget(self._icon)
        row.addWidget(self._text, 1)
        row.addWidget(dismiss)

    def show_message(self, message: str) -> None:
        self._text.setText(message)
        self.setVisible(True)

    def hide_message(self) -> None:
        self.setVisible(False)

    def _dismiss(self) -> None:
        self.hide_message()
        if self._on_dismiss is not None:
            self._on_dismiss()
