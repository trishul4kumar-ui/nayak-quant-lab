"""Responsive, read-only candidate intake queue."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from quantlab.trade_candidates.models import CandidateStatus, TradeCandidatePacket
from quantlab.trade_candidates.ranking import rank_for_review


class TradeQueueWorkspace(QWidget):
    """Central intake; selecting a row never stages, approves, or routes an order."""

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        self.summary = QLabel("No candidate packets · NO EXECUTION AUTHORITY")
        self.summary.setWordWrap(True)
        layout.addWidget(self.summary)
        controls = QHBoxLayout()
        self.filter = QComboBox()
        self.filter.addItems(["ALL", "READY", "WATCH", "BLOCKED", "EXPIRED", "LONG", "BEARISH"])
        controls.addWidget(QLabel("Filter:"))
        controls.addWidget(self.filter)
        controls.addStretch(1)
        layout.addLayout(controls)
        self.table = QTableWidget(0, 10)
        self.table.setHorizontalHeaderLabels(
            [
                "Symbol",
                "Stance",
                "Bull",
                "Bear",
                "Adjudication",
                "Validation",
                "Risk",
                "Freshness",
                "Status",
                "Age",
            ]
        )
        self.table.setAccessibleName("Immutable research candidate intake queue")
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.table, 1)
        self.filter.currentTextChanged.connect(self._apply_filter)
        self._candidates: tuple[TradeCandidatePacket, ...] = ()

    def set_candidates(self, candidates: tuple[TradeCandidatePacket, ...]) -> None:
        self._candidates = rank_for_review(candidates)
        self._apply_filter(self.filter.currentText())

    def _apply_filter(self, selected: str) -> None:
        rows = self._candidates
        if selected == "READY":
            rows = tuple(row for row in rows if row.status is CandidateStatus.READY_FOR_REVIEW)
        elif selected in {"WATCH", "BLOCKED", "EXPIRED"}:
            rows = tuple(row for row in rows if row.status.value == selected)
        elif selected in {"LONG", "BEARISH"}:
            rows = tuple(row for row in rows if row.stance.value == selected)
        self.table.setRowCount(len(rows))
        for index, candidate in enumerate(rows):
            statuses = {summary.category: summary.status.value for summary in candidate.summaries}
            values = (
                candidate.security_id,
                candidate.stance.value,
                f"{candidate.raw_bull_confidence:.2f}",
                f"{candidate.raw_bear_confidence:.2f}",
                candidate.adjudication_hash[:8],
                statuses.get("validation", "UNKNOWN"),
                statuses.get("portfolio_risk", "UNKNOWN"),
                candidate.data_freshness,
                candidate.status.value,
                candidate.created_at.isoformat(),
            )
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(256, candidate.content_hash)
                self.table.setItem(index, column, item)
        self.summary.setText(
            f"{len(rows)} visible candidate packets · ranking is attention-only · "
            "NO EXECUTION AUTHORITY"
        )
