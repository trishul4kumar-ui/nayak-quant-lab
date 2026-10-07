"""Canonical native viewer for immutable paper/shadow position reviews."""

from __future__ import annotations

import json

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from quantlab.position_intelligence.models import PositionAssessment


class PositionReviewWorkspace(QWidget):
    """Review proposals only; buttons request an audit event and never mutate a position."""

    reviewAction = Signal(str, str)

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        self.summary = QLabel("No paper/shadow position reviews · NO EXECUTION AUTHORITY")
        self.summary.setWordWrap(True)
        layout.addWidget(self.summary)
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            ["Position", "Thesis", "Suggested stance", "Confidence", "Blockers"]
        )
        self.table.setAccessibleName("Immutable position review history")
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.cellClicked.connect(self._show_row)
        layout.addWidget(self.table, 1)
        self.details = QTextBrowser()
        self.details.setAccessibleName("Position review evidence and deterministic exit state")
        layout.addWidget(self.details, 1)
        controls = QHBoxLayout()
        for label, action in (
            ("KEEP", "KEEP_REQUESTED"),
            ("CREATE REDUCE CANDIDATE", "REDUCE_CANDIDATE_REQUESTED"),
            ("CREATE EXIT CANDIDATE", "EXIT_CANDIDATE_REQUESTED"),
            ("REFRESH", "REFRESH_REQUESTED"),
        ):
            button = QPushButton(label)
            button.clicked.connect(lambda _checked=False, value=action: self._request(value))
            controls.addWidget(button)
        controls.addStretch(1)
        layout.addLayout(controls)
        self._assessments: tuple[PositionAssessment, ...] = ()

    def set_assessments(self, assessments: tuple[PositionAssessment, ...]) -> None:
        self._assessments = assessments
        self.table.setRowCount(len(assessments))
        for row, assessment in enumerate(assessments):
            values = (
                assessment.position_id,
                assessment.thesis_status,
                assessment.suggested_stance.value,
                f"{assessment.confidence:.2f}",
                ", ".join(assessment.hard_blockers) or "None",
            )
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(256, assessment.content_hash)
                self.table.setItem(row, column, item)
        self.summary.setText(
            f"{len(assessments)} immutable review(s) · proposals re-enter research · "
            "NO EXECUTION AUTHORITY"
        )
        self.details.clear()

    def _show_row(self, row: int, _: int) -> None:
        if not 0 <= row < len(self._assessments):
            return
        assessment = self._assessments[row]
        self.details.setPlainText(json.dumps(assessment.model_dump(mode="json"), indent=2))

    def _request(self, action: str) -> None:
        current = self.table.currentRow()
        if not 0 <= current < len(self._assessments):
            self.summary.setText("Select an immutable review first; no action was taken.")
            return
        self.reviewAction.emit(action, self._assessments[current].content_hash)
