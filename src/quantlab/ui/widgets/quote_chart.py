"""Native time-scaled plot of actual observed Kite quotes, not historical candles."""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRect, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPaintEvent, QPen
from PySide6.QtWidgets import QWidget

from quantlab.app.live_market import IST, QuotePoint
from quantlab.ui.theme import chart_palette


class QuoteTrendWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._points: list[QuotePoint] = []
        self._instrument = ""
        self.setMinimumHeight(180)
        self.setAccessibleName("Observed quote value in provider units by provider timestamp, IST")

    def set_points(self, instrument: str, points: list[QuotePoint]) -> None:
        self._instrument = instrument
        self._points = list(points)
        self.setToolTip(
            "Kite REST quote samples received in this app session. "
            "Not candles, historical data, or tick-by-tick coverage. Gaps are not interpolated."
        )
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802
        del event
        painter = QPainter(self)
        palette = chart_palette()
        painter.fillRect(self.rect(), QColor(palette.background))
        painter.setPen(QColor(palette.muted))
        if not self._points:
            painter.drawText(
                self.rect(),
                Qt.AlignmentFlag.AlignCenter,
                "No fresh observed samples for this instrument yet\n"
                "Only valid, provider-timestamped quotes enter the trend",
            )
            return
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        plot = QRect(76, 30, max(1, self.width() - 96), max(1, self.height() - 65))
        prices = [point.price for point in self._points]
        lo, hi = min(prices), max(prices)
        pad = max((hi - lo) * 0.08, 0.05)
        lo, hi = lo - pad, hi + pad
        begin = self._points[0].time.timestamp()
        end = self._points[-1].time.timestamp()
        span = max(end - begin, 1.0)
        painter.drawText(8, 19, f"{self._instrument} · LTP / value · observed samples only")
        for fraction in (0.0, 0.5, 1.0):
            y = plot.top() + fraction * plot.height()
            painter.setPen(QPen(QColor(palette.muted), 0.5, Qt.PenStyle.DotLine))
            painter.drawLine(QPointF(plot.left(), y), QPointF(plot.right(), y))
            painter.setPen(QColor(palette.muted))
            painter.drawText(2, int(y) + 4, f"{hi - fraction * (hi - lo):,.2f}")
        painter.drawText(
            plot.left(),
            self.height() - 10,
            self._points[0].time.astimezone(IST).strftime("%d %b %H:%M:%S IST"),
        )
        if len(self._points) > 1:
            painter.drawText(
                QRect(plot.left(), self.height() - 25, plot.width(), 20),
                Qt.AlignmentFlag.AlignRight,
                self._points[-1].time.astimezone(IST).strftime("%H:%M:%S IST"),
            )
        path = QPainterPath()
        previous: QuotePoint | None = None
        for point in self._points:
            x = plot.left() + (point.time.timestamp() - begin) / span * plot.width()
            y = plot.top() + (hi - point.price) / (hi - lo) * plot.height()
            disconnected = (
                previous is None
                or previous.segment != point.segment
                or (point.time - previous.time).total_seconds() > 10
            )
            if disconnected:
                path.moveTo(x, y)
            else:
                path.lineTo(x, y)
            painter.setPen(QPen(QColor("#42a5f5"), 2))
            painter.drawEllipse(QPointF(x, y), 2, 2)
            previous = point
        painter.drawPath(path)
