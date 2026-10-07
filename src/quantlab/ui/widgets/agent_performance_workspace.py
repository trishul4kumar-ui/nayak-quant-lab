"""Native statistical view of frozen agent scorecards."""

from __future__ import annotations

import json

from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QTextBrowser, QVBoxLayout, QWidget

from quantlab.agent_calibration.models import AgentScorecard


class AgentPerformanceWorkspace(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(
            ["Agent", "Version", "Status", "Samples", "Brier", "Hit rate", "Calibrated"]
        )
        self.table.setAccessibleName("Frozen agent calibration scorecards")
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.cellClicked.connect(self._show_row)
        layout.addWidget(self.table, 1)
        self.details = QTextBrowser()
        self.details.setAccessibleName("Reliability bins, regime breakdown, and warnings")
        layout.addWidget(self.details, 1)
        self._scorecards: tuple[AgentScorecard, ...] = ()

    def set_scorecards(self, scorecards: tuple[AgentScorecard, ...]) -> None:
        self._scorecards = scorecards
        self.table.setRowCount(len(scorecards))
        for row, scorecard in enumerate(scorecards):
            values = (
                scorecard.agent_id,
                scorecard.agent_version,
                scorecard.status.value,
                str(scorecard.sample_size),
                self._number(scorecard.brier_score),
                self._number(scorecard.hit_rate),
                self._number(scorecard.calibrated_confidence),
            )
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(256, scorecard.content_hash)
                self.table.setItem(row, column, item)
        self.details.clear()

    @staticmethod
    def _number(value: float | None) -> str:
        return "NOT TESTED" if value is None else f"{value:.3f}"

    def _show_row(self, row: int, _: int) -> None:
        if 0 <= row < len(self._scorecards):
            self.details.setPlainText(
                json.dumps(self._scorecards[row].model_dump(mode="json"), indent=2)
            )
