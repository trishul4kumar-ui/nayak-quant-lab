from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QWidget

from quantlab.ui.theme import chart_palette


class EquityCurveWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._values: list[float] = []
        self.setMinimumHeight(220)
        self.setObjectName("equity-curve")

    def set_values(self, values: list[float]) -> None:
        self._values = list(values)
        self.update()

    def paintEvent(self, event: object) -> None:  # noqa: ARG002
        pal = chart_palette()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(pal.background))
        if len(self._values) < 2:
            painter.setPen(QColor(pal.muted))
            painter.drawText(
                self.rect(),
                Qt.AlignmentFlag.AlignCenter,
                "Run a backtest to see the equity curve",
            )
            return
        lo = min(self._values)
        hi = max(self._values)
        span = hi - lo if hi != lo else 1.0
        pad = 16
        width = max(self.width() - 2 * pad, 1)
        height = max(self.height() - 2 * pad, 1)
        path = QPainterPath()
        for i, value in enumerate(self._values):
            x = pad + width * i / (len(self._values) - 1)
            y = pad + height * (1.0 - (value - lo) / span)
            if i == 0:
                path.moveTo(x, y)
            else:
                path.lineTo(x, y)
        painter.setPen(QPen(QColor("#42a5f5"), 2))
        painter.drawPath(path)
        painter.setPen(QColor(pal.muted))
        painter.drawText(QRectF(8, 4, 200, 16), f"start {self._values[0]:,.0f}")
        painter.drawText(
            QRectF(self.width() - 160, 4, 150, 16),
            Qt.AlignmentFlag.AlignRight,
            f"end {self._values[-1]:,.0f}",
        )


def fill_table(table: QTableWidget, headers: list[str], rows: list[list[str]]) -> None:
    table.clear()
    table.setColumnCount(len(headers))
    table.setHorizontalHeaderLabels(headers)
    table.setRowCount(len(rows))
    table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    table.setAlternatingRowColors(False)
    table.setShowGrid(False)
    for r, row in enumerate(rows):
        for c, cell in enumerate(row):
            table.setItem(r, c, QTableWidgetItem(cell))
    table.resizeColumnsToContents()
