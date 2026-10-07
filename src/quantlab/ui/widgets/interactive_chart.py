"""Native financial chart: navigation, inspection and display-only drawings."""

from __future__ import annotations

from bisect import bisect_left
from dataclasses import dataclass
from datetime import datetime

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import (
    QColor,
    QKeyEvent,
    QMouseEvent,
    QPainter,
    QPainterPath,
    QPaintEvent,
    QPen,
    QWheelEvent,
)
from PySide6.QtWidgets import QWidget

from quantlab.app.chart_indicators import bollinger, ema, rsi, sma
from quantlab.app.live_market import IST, QuotePoint, display_time
from quantlab.realtime_data.candles import INTERVALS, CandleSeries
from quantlab.ui.theme import chart_palette


@dataclass(frozen=True)
class Drawing:
    kind: str
    start: tuple[float, float]
    end: tuple[float, float]


class InteractivePriceChart(QWidget):
    inspected = Signal(str)
    navigation_changed = Signal(bool)
    drawings_changed = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setMinimumSize(320, 260)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAccessibleName("Interactive quote and candle values in provider units, IST")
        self.setToolTip(
            "Wheel: zoom · drag: pan · arrows: inspect · +/-: zoom · Home: fit · End: latest"
        )
        self._instrument = ""
        self.series: CandleSeries | None = None
        self.samples: list[QuotePoint] = []
        self.view = "Candles"
        self.show_volume = True
        self.indicators: set[str] = {"EMA 9", "EMA 26"}
        self.tool = "Crosshair"
        self.drawings: list[Drawing] = []
        self._pending_draw: tuple[float, float] | None = None
        self._hover: QPointF | None = None
        self._drag: tuple[float, float] | None = None
        self._xs: list[float] = []
        self._values: list[float] = []
        self._times: list[datetime] = []
        self._overlays: dict[str, list[float | None]] = {}
        self._rsi: list[float | None] = []
        self._start = -0.5
        self._span = 120.0
        self.follow = True
        self.live_price: float | None = None
        self.live_quality = "missing"
        self._lo, self._hi = 0.0, 1.0
        self._price_rect = QRectF()
        self._empty = "Select an instrument and connect Kite to load candles"

    def set_series(
        self, instrument: str, series: CandleSeries | None, samples: list[QuotePoint] | None = None
    ) -> None:
        changed = (
            instrument != self._instrument
            or (
                series is not None
                and self.series is not None
                and series.request != self.series.request
            )
            or (bool(samples) != bool(self.samples) and series is None)
        )
        if series and self.series and series.candles and self.series.candles:
            changed = changed or series.candles[0].time != self.series.candles[0].time
        self._instrument = instrument
        self.series = series
        self.samples = list(samples or [])
        if series is not None:
            self._xs = [float(i) for i in range(len(series.candles))]
            self._values = [row.close for row in series.candles]
            self._times = [row.time for row in series.candles]
        else:
            self._xs = [row.time.timestamp() for row in self.samples]
            self._values = [row.price for row in self.samples]
            self._times = [row.time for row in self.samples]
        self._overlays = {}
        self._rsi = []
        if series is not None:
            self._overlays = {
                "SMA 20": sma(self._values, 20),
                "EMA 9": ema(self._values, 9),
                "EMA 26": ema(self._values, 26),
            }
            upper, lower = bollinger(self._values)
            self._overlays["BB upper"], self._overlays["BB lower"] = upper, lower
            self._rsi = rsi(self._values)
        if changed:
            self.drawings.clear()
            self._pending_draw = None
            self.drawings_changed.emit()
            self._hover = None
            self.follow = True
        if self.follow:
            self.latest()
        self.update()

    def latest(self) -> None:
        self.follow = True
        if self._xs:
            if self.series is not None:
                self._span = min(max(20.0, self._span), max(20.0, len(self._xs)))
                self._start = self._xs[-1] - self._span + 3
            else:
                self._span = min(max(60.0, self._span), max(60.0, self._xs[-1] - self._xs[0] + 10))
                self._start = self._xs[-1] - self._span + 5
        self.navigation_changed.emit(True)
        self.update()

    def fit(self) -> None:
        self.follow = False
        if self._xs:
            pad = 1 if self.series is not None else 2
            self._start = self._xs[0] - pad
            self._span = max(self._xs[-1] - self._xs[0] + 2 * pad, 4 if self.series else 10)
        self.navigation_changed.emit(False)
        self.update()

    def zoom(self, factor: float, anchor: float = 0.5) -> None:
        minimum = 8.0 if self.series else 10.0
        maximum = max(20.0, (self._xs[-1] - self._xs[0] + 20) * 2) if self._xs else 1000.0
        new_span = min(maximum, max(minimum, self._span * factor))
        self._start += (self._span - new_span) * anchor
        self._span = new_span
        self.follow = False
        self.navigation_changed.emit(False)
        self.update()

    def _indices(self) -> list[int]:
        return [i for i, x in enumerate(self._xs) if self._start <= x <= self._start + self._span]

    def _x(self, value: float) -> float:
        return (
            self._price_rect.left() + (value - self._start) / self._span * self._price_rect.width()
        )

    def _y(self, value: float) -> float:
        return (
            self._price_rect.bottom()
            - (value - self._lo) / (self._hi - self._lo) * self._price_rect.height()
        )

    def _data_at(self, point: QPointF) -> tuple[float, float]:
        rect = self._price_rect
        return (
            self._start + (point.x() - rect.left()) / max(rect.width(), 1) * self._span,
            self._hi - (point.y() - rect.top()) / max(rect.height(), 1) * (self._hi - self._lo),
        )

    def _nearest(self, x: float) -> int:
        pos = bisect_left(self._xs, x)
        choices = [i for i in (pos - 1, pos) if 0 <= i < len(self._xs)]
        return min(choices, key=lambda i: abs(self._xs[i] - x))

    def inspection(self, index: int) -> str:
        if self.series is not None:
            row = self.series.candles[index]
            volume = "—" if row.volume is None else f"{row.volume:,.0f}"
            state = " · forming / may revise" if self.series.is_forming(row) else ""
            return (
                f"{display_time(row.time)} · O {row.open:,.2f}  H {row.high:,.2f}  "
                f"L {row.low:,.2f}  C {row.close:,.2f} · Vol {volume}{state}"
            )
        return f"{display_time(self._times[index])} · observed LTP {self._values[index]:,.2f}"

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802
        del event
        p = QPainter(self)
        palette = chart_palette()
        p.fillRect(self.rect(), QColor(palette.background))
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(QColor(palette.muted))
        if not self._xs:
            p.drawText(
                QRectF(self.rect()).adjusted(20, 20, -20, -20),
                Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap,
                self._empty,
            )
            return
        volume_height = 54 if self.show_volume and self.series else 0
        rsi_height = 70 if "RSI 14" in self.indicators and self.series else 0
        self._price_rect = QRectF(
            12,
            24,
            max(1, self.width() - 100),
            max(70, self.height() - 58 - volume_height - rsi_height),
        )
        rect = self._price_rect
        visible = self._indices()
        if not visible:
            p.drawText(rect, Qt.AlignmentFlag.AlignCenter, "No bars in this viewport · Home to fit")
            return
        lows = [self.series.candles[i].low if self.series else self._values[i] for i in visible]
        highs = [self.series.candles[i].high if self.series else self._values[i] for i in visible]
        for name, values in self._overlays.items():
            if name in self.indicators or (name.startswith("BB") and "BB 20" in self.indicators):
                points = [values[i] for i in visible if values[i] is not None]
                lows.extend(value for value in points if value is not None)
                highs.extend(value for value in points if value is not None)
        lo, hi = min(lows), max(highs)
        pad = max((hi - lo) * 0.08, abs(hi) * 0.0001, 0.01)
        self._lo, self._hi = lo - pad, hi + pad
        p.drawText(12, 16, f"{self._instrument} · provider units · IST")
        for fraction in (0.0, 0.25, 0.5, 0.75, 1.0):
            y = rect.top() + fraction * rect.height()
            p.setPen(QPen(QColor(palette.grid), 1, Qt.PenStyle.DotLine))
            p.drawLine(QPointF(rect.left(), y), QPointF(rect.right(), y))
            p.setPen(QColor(palette.muted))
            p.drawText(
                QRectF(rect.right() + 5, y - 8, 80, 18),
                Qt.AlignmentFlag.AlignLeft,
                f"{self._hi - fraction * (self._hi - self._lo):,.2f}",
            )
        p.save()
        p.setClipRect(rect)
        if self.series is not None and self.view in {"Candles", "OHLC"}:
            width = min(18.0, max(1.0, rect.width() / self._span * 0.65))
            for i in visible:
                row = self.series.candles[i]
                x = self._x(self._xs[i])
                color = QColor("#26a69a" if row.close >= row.open else "#ef5350")
                p.setPen(QPen(color, 1))
                p.drawLine(QPointF(x, self._y(row.high)), QPointF(x, self._y(row.low)))
                if self.view == "OHLC":
                    p.drawLine(
                        QPointF(x - width / 2, self._y(row.open)), QPointF(x, self._y(row.open))
                    )
                    p.drawLine(
                        QPointF(x, self._y(row.close)), QPointF(x + width / 2, self._y(row.close))
                    )
                else:
                    p.setBrush(QColor(palette.background) if row.close >= row.open else color)
                    top, bottom = sorted((self._y(row.open), self._y(row.close)))
                    p.drawRect(QRectF(x - width / 2, top, width, max(1, bottom - top)))
        else:
            self._curve(p, visible, list(self._values), "#42a5f5", area=self.view == "Area")
        for name, line_color in (
            ("SMA 20", "#c4a76b"),
            ("EMA 9", "#42a5f5"),
            ("EMA 26", "#8bc34a"),
            ("BB upper", "#9575cd"),
            ("BB lower", "#9575cd"),
        ):
            enabled = name in self.indicators or (
                name.startswith("BB") and "BB 20" in self.indicators
            )
            if enabled and name in self._overlays:
                self._curve(p, visible, self._overlays[name], line_color)
        if self.live_price is not None and self._lo <= self.live_price <= self._hi:
            color = QColor("#26a69a" if self.live_quality == "valid" else "#ffb74d")
            p.setPen(QPen(color, 1, Qt.PenStyle.DashLine))
            p.drawLine(
                QPointF(rect.left(), self._y(self.live_price)),
                QPointF(rect.right(), self._y(self.live_price)),
            )
        p.setPen(QPen(QColor("#f6c667"), 1, Qt.PenStyle.DashLine))
        for drawing in self.drawings:
            a, b = drawing.start, drawing.end
            if drawing.kind == "Horizontal":
                p.drawLine(
                    QPointF(rect.left(), self._y(a[1])), QPointF(rect.right(), self._y(a[1]))
                )
            else:
                p.drawLine(
                    QPointF(self._x(a[0]), self._y(a[1])), QPointF(self._x(b[0]), self._y(b[1]))
                )
        p.restore()
        if self.live_price is not None and self._lo <= self.live_price <= self._hi:
            color = QColor("#26a69a" if self.live_quality == "valid" else "#ffb74d")
            quote_y = self._y(self.live_price)
            p.fillRect(QRectF(rect.right(), quote_y - 9, 85, 18), color)
            p.setPen(QColor(palette.background))
            p.drawText(QPointF(rect.right() + 4, quote_y + 4), f"Q {self.live_price:,.2f}")
        bottom = rect.bottom() + 6
        if volume_height and self.series:
            volumes = [self.series.candles[i].volume for i in visible]
            peak = max((v for v in volumes if v is not None), default=0.0)
            p.setPen(QColor(palette.muted))
            p.drawText(
                14,
                int(bottom) + 12,
                "Volume · zero baseline"
                if peak
                else (
                    "Volume · returned values zero"
                    if any(v is not None for v in volumes)
                    else "Volume unavailable"
                ),
            )
            for i in visible:
                row = self.series.candles[i]
                if row.volume is not None and peak > 0:
                    height = row.volume / peak * (volume_height - 16)
                    color = QColor("#26a69a" if row.close >= row.open else "#ef5350")
                    p.fillRect(
                        QRectF(
                            self._x(self._xs[i]) - 2,
                            bottom + volume_height - height,
                            max(1, min(12, rect.width() / self._span * 0.65)),
                            height,
                        ),
                        color,
                    )
            bottom += volume_height
        if rsi_height:
            rsi_rect = QRectF(rect.left(), bottom + 6, rect.width(), rsi_height - 10)
            p.setPen(QColor(palette.muted))
            p.drawText(14, int(rsi_rect.top()) + 12, "RSI 14 · Wilder · 0–100")
            p.save()
            p.setClipRect(rsi_rect)
            for level in (30, 70):
                y = rsi_rect.bottom() - level / 100 * rsi_rect.height()
                p.setPen(QPen(QColor(palette.grid), 1, Qt.PenStyle.DashLine))
                p.drawLine(QPointF(rect.left(), y), QPointF(rect.right(), y))
            p.restore()
            p.setPen(QColor(palette.muted))
            for level in (30, 70):
                y = rsi_rect.bottom() - level / 100 * rsi_rect.height()
                p.drawText(QPointF(rect.right() + 5, y + 4), str(level))
            p.save()
            p.setClipRect(rsi_rect)
            path = QPainterPath()
            begun = False
            for i in visible:
                value = self._rsi[i]
                if value is None:
                    continue
                point = QPointF(
                    self._x(self._xs[i]), rsi_rect.bottom() - value / 100 * rsi_rect.height()
                )
                if not begun:
                    path.moveTo(point)
                    begun = True
                else:
                    path.lineTo(point)
            p.setPen(QPen(QColor("#9575cd"), 1.5))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawPath(path)
            p.restore()
        self._axis(p, visible)
        if self._hover and rect.contains(self._hover):
            x, value = self._data_at(self._hover)
            index = self._nearest(x)
            p.setPen(QPen(QColor(palette.muted), 1, Qt.PenStyle.DashLine))
            p.drawLine(
                QPointF(self._x(self._xs[index]), rect.top()),
                QPointF(self._x(self._xs[index]), rect.bottom()),
            )
            p.drawLine(
                QPointF(rect.left(), self._hover.y()), QPointF(rect.right(), self._hover.y())
            )
            label = f"{value:,.2f}"
            p.fillRect(QRectF(rect.right(), self._hover.y() - 10, 85, 20), QColor(palette.grid))
            p.setPen(QColor(palette.foreground))
            p.drawText(QPointF(rect.right() + 4, self._hover.y() + 4), label)

    def _curve(
        self,
        p: QPainter,
        visible: list[int],
        values: list[float | None],
        color: str,
        *,
        area: bool = False,
    ) -> None:
        p.setBrush(Qt.BrushStyle.NoBrush)
        path = QPainterPath()
        runs: list[list[QPointF]] = []
        previous: int | None = None
        for i in visible:
            if values[i] is None:
                previous = None
                continue
            value = values[i]
            assert value is not None
            point = QPointF(self._x(self._xs[i]), self._y(value))
            gap = previous is None
            if previous is not None:
                gap = (
                    (self._times[i] - self._times[previous]).total_seconds()
                    > (INTERVALS[self.series.request.interval] * 1.5 if self.series else 10)
                ) or (not self.series and self.samples[i].segment != self.samples[previous].segment)
            if gap:
                path.moveTo(point)
                runs.append([point])
            else:
                path.lineTo(point)
                runs[-1].append(point)
            previous = i
        # Separate fills ensure a paused/missing/session gap is never bridged.
        if area:
            for run in runs:
                if len(run) < 2:
                    continue
                fill = QPainterPath(run[0])
                for point in run[1:]:
                    fill.lineTo(point)
                fill.lineTo(run[-1].x(), self._price_rect.bottom())
                fill.lineTo(run[0].x(), self._price_rect.bottom())
                fill.closeSubpath()
                tint = QColor(color)
                tint.setAlpha(35)
                p.fillPath(fill, tint)
        p.setPen(QPen(QColor(color), 1.5))
        p.drawPath(path)
        for run in runs:
            if len(run) == 1:
                p.drawEllipse(run[0], 2.5, 2.5)

    def _axis(self, p: QPainter, visible: list[int]) -> None:
        p.setPen(QColor(chart_palette().muted))
        count = max(2, min(5, int(self._price_rect.width() / 155)))
        used: set[int] = set()
        for n in range(count):
            i = visible[round(n * (len(visible) - 1) / (count - 1))]
            if i in used:
                continue
            used.add(i)
            text = self._times[i].astimezone(IST).strftime("%d %b %H:%M")
            width = 120.0
            left = min(
                max(self._x(self._xs[i]) - width / 2, self._price_rect.left()),
                self._price_rect.right() - width,
            )
            p.drawText(
                QRectF(left, self.height() - 22, width, 20), Qt.AlignmentFlag.AlignCenter, text
            )

    def wheelEvent(self, event: QWheelEvent) -> None:  # noqa: N802
        rect = self._price_rect
        if rect.contains(event.position()):
            self.zoom(
                0.8 if event.angleDelta().y() > 0 else 1.25,
                (event.position().x() - rect.left()) / max(1, rect.width()),
            )
            event.accept()

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if event.button() != Qt.MouseButton.LeftButton or not self._price_rect.contains(
            event.position()
        ):
            return
        self.setFocus()
        point = self._data_at(event.position())
        if self.tool == "Horizontal":
            self.drawings.append(Drawing(self.tool, point, point))
        elif self.tool == "Trend line":
            if self._pending_draw is None:
                self._pending_draw = point
            else:
                self.drawings.append(Drawing(self.tool, self._pending_draw, point))
                self._pending_draw = None
        else:
            self._drag = (event.position().x(), self._start)
        self.drawings = self.drawings[-100:]
        self.drawings_changed.emit()
        self.update()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        self._hover = event.position()
        if self._drag:
            self._start = (
                self._drag[1]
                - (event.position().x() - self._drag[0])
                / max(1, self._price_rect.width())
                * self._span
            )
            self.follow = False
            self.navigation_changed.emit(False)
        if self._xs and self._price_rect.contains(event.position()):
            self.inspected.emit(self.inspection(self._nearest(self._data_at(event.position())[0])))
        self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        del event
        self._drag = None

    def leaveEvent(self, event: object) -> None:  # noqa: N802
        del event
        self._hover = None
        self.update()

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        key = event.key()
        if key in (Qt.Key.Key_Plus, Qt.Key.Key_Equal, Qt.Key.Key_Minus):
            self.zoom(1.25 if key == Qt.Key.Key_Minus else 0.8)
        elif key == Qt.Key.Key_Home:
            self.fit()
        elif key == Qt.Key.Key_End:
            self.latest()
        elif key == Qt.Key.Key_Escape:
            self._pending_draw = None
            self.drawings_changed.emit()
        elif key in (Qt.Key.Key_Left, Qt.Key.Key_Right) and self._xs:
            current = (
                self._nearest(self._data_at(self._hover)[0]) if self._hover else len(self._xs) - 1
            )
            index = max(0, min(len(self._xs) - 1, current + (-1 if key == Qt.Key.Key_Left else 1)))
            x = self._xs[index]
            if x < self._start or x > self._start + self._span:
                self._start = x - self._span * (0.25 if key == Qt.Key.Key_Left else 0.75)
                self.follow = False
                self.navigation_changed.emit(False)
            self._hover = QPointF(self._x(self._xs[index]), self._y(self._values[index]))
            self.inspected.emit(self.inspection(index))
            self.update()
        else:
            super().keyPressEvent(event)
