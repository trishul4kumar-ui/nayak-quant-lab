"""Reusable dashboard charts — PySide6 QPainter, no third-party plot libs."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPaintEvent, QPen, QShowEvent
from PySide6.QtWidgets import QFrame, QGridLayout, QLabel, QVBoxLayout, QWidget

from quantlab.ui.responsive import ResponsiveState, responsive_state
from quantlab.ui.theme import chart_palette

SERIES_COLORS = ("#42a5f5", "#66bb6a", "#ffa726", "#ef5350", "#ab47bc", "#26c6da")


@dataclass(frozen=True)
class ChartSeries:
    label: str
    values: list[float]
    color: str = SERIES_COLORS[0]
    dashed: bool = False


def _series_bounds(series: list[ChartSeries]) -> tuple[float, float]:
    values = [v for s in series for v in s.values if s.values]
    if not values:
        return 0.0, 1.0
    lo, hi = min(values), max(values)
    if lo == hi:
        return lo - 1.0, hi + 1.0
    pad = (hi - lo) * 0.05
    return lo - pad, hi + pad


def _paint_line_path(
    painter: QPainter,
    rect: QRect,
    values: list[float],
    *,
    color: str,
    lo: float | None = None,
    hi: float | None = None,
    fill_under: bool = False,
    fill_color: str | None = None,
    dashed: bool = False,
) -> None:
    if len(values) < 2:
        return
    if lo is None or hi is None:
        lo = min(values)
        hi = max(values)
        span = hi - lo if hi != lo else 1.0
    else:
        span = hi - lo if hi != lo else 1.0
    pad = 8
    width = max(rect.width() - 2 * pad, 1)
    height = max(rect.height() - 2 * pad, 1)

    path = QPainterPath()
    for i, value in enumerate(values):
        x = rect.x() + pad + width * i / (len(values) - 1)
        y = rect.y() + pad + height * (1.0 - (value - lo) / span)
        if i == 0:
            path.moveTo(x, y)
        else:
            path.lineTo(x, y)

    if fill_under:
        fill_path = QPainterPath(path)
        fill_path.lineTo(rect.x() + pad + width, rect.y() + pad + height)
        fill_path.lineTo(rect.x() + pad, rect.y() + pad + height)
        fill_path.closeSubpath()
        painter.fillPath(fill_path, QColor(fill_color or color).darker(180))

    painter.setPen(
        QPen(QColor(color), 2, Qt.PenStyle.DashLine if dashed else Qt.PenStyle.SolidLine)
    )
    painter.drawPath(path)


def _paint_empty(painter: QPainter, rect: QRect, message: str) -> None:
    painter.setPen(QColor(chart_palette().muted))
    painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, message)


class SparklineWidget(QWidget):
    """Compact inline trend chart."""

    def __init__(self, *, min_height: int = 56) -> None:
        super().__init__()
        self._values: list[float] = []
        self._color = SERIES_COLORS[0]
        self._empty = "No data"
        self.setMinimumHeight(min_height)
        self.setObjectName("sparkline")

    def set_values(self, values: list[float], *, color: str = SERIES_COLORS[0]) -> None:
        self._values = list(values)
        self._color = color
        self.update()

    def set_empty_message(self, message: str) -> None:
        self._empty = message
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: ARG002
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pal = chart_palette()
        painter.fillRect(self.rect(), QColor(pal.background))
        if len(self._values) < 2:
            _paint_empty(painter, self.rect(), self._empty)
            return
        _paint_line_path(painter, self.rect(), self._values, color=self._color)


class MultiSeriesChartWidget(QWidget):
    """Overlay multiple normalized series (e.g. compare equity curves)."""

    def __init__(self) -> None:
        super().__init__()
        self._series: list[ChartSeries] = []
        self._empty = "Select runs to compare curves"
        self.setMinimumHeight(220)
        self.setObjectName("multi-series-chart")

    def set_series(self, series: list[ChartSeries]) -> None:
        self._series = list(series)
        self.update()

    def set_empty_message(self, message: str) -> None:
        self._empty = message
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: ARG002
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect()
        pal = chart_palette()
        painter.fillRect(rect, QColor(pal.background))
        if not self._series:
            _paint_empty(painter, rect, self._empty)
            return
        plot = rect.adjusted(0, 22, 0, 0)
        lo, hi = _series_bounds(self._series)
        legend_x = 10
        for i, item in enumerate(self._series):
            if len(item.values) < 2:
                continue
            _paint_line_path(
                painter,
                plot,
                item.values,
                color=item.color,
                lo=lo,
                hi=hi,
                dashed=item.dashed,
            )
            painter.setPen(QColor(item.color))
            painter.drawText(legend_x + i * 130, 16, item.label[:16])
        if all(len(s.values) < 2 for s in self._series):
            _paint_empty(painter, rect, self._empty)


class DrawdownChartWidget(QWidget):
    """Underwater drawdown chart (0 at top, negative below)."""

    def __init__(self) -> None:
        super().__init__()
        self._values: list[float] = []
        self.setMinimumHeight(160)
        self.setObjectName("drawdown-chart")

    def set_drawdown(self, values: list[float]) -> None:
        self._values = list(values)
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: ARG002
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect()
        pal = chart_palette()
        painter.fillRect(rect, QColor(pal.background))
        if len(self._values) < 2:
            _paint_empty(painter, rect, "Run a backtest to see drawdown")
            return
        lo = min(self._values)
        hi = 0.0
        span = hi - lo if hi != lo else 1.0
        pad = 12
        width = max(rect.width() - 2 * pad, 1)
        height = max(rect.height() - 2 * pad, 1)
        zero_y = rect.y() + pad + height * (1.0 - (0.0 - lo) / span)
        path = QPainterPath()
        for i, value in enumerate(self._values):
            x = rect.x() + pad + width * i / (len(self._values) - 1)
            y = rect.y() + pad + height * (1.0 - (value - lo) / span)
            if i == 0:
                path.moveTo(x, y)
            else:
                path.lineTo(x, y)
        fill = QPainterPath(path)
        fill.lineTo(rect.x() + pad + width, int(zero_y))
        fill.lineTo(rect.x() + pad, int(zero_y))
        fill.closeSubpath()
        painter.fillPath(fill, QColor("#ef5350").darker(180))
        painter.setPen(QPen(QColor("#ef5350"), 2))
        painter.drawPath(path)
        worst = min(self._values)
        pal = chart_palette()
        painter.setPen(QColor(pal.muted))
        painter.drawText(rect.x() + 8, rect.y() + 16, f"worst {worst:.1%}")


class BarChartWidget(QWidget):
    """Horizontal bar chart for metric comparison."""

    def __init__(self) -> None:
        super().__init__()
        self._items: list[tuple[str, float, str]] = []
        self.setMinimumHeight(120)
        self.setObjectName("bar-chart")

    def set_items(self, items: list[tuple[str, float, str]]) -> None:
        """Each item: (label, value, color hex)."""
        self._items = list(items)
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: ARG002
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect()
        pal = chart_palette()
        painter.fillRect(rect, QColor(pal.background))
        if not self._items:
            _paint_empty(painter, rect, "No metrics to chart")
            return
        max_abs = max(abs(v) for _, v, _ in self._items) or 1.0
        row_h = max((rect.height() - 16) // len(self._items), 22)
        y = 8
        label_w = 72
        bar_x = rect.x() + label_w + 8
        bar_max_w = max(rect.width() - label_w - 80, 40)
        for label, value, color in self._items:
            painter.setPen(QColor(pal.muted))
            painter.drawText(rect.x() + 8, y + 14, label[:10])
            bar_w = int(bar_max_w * min(abs(value) / max_abs, 1.0))
            painter.fillRect(bar_x, y + 4, bar_w, row_h - 10, QColor(color))
            painter.setPen(QColor(pal.foreground))
            painter.drawText(bar_x + bar_w + 6, y + 14, f"{value:.3f}")
            y += row_h


class ScatterChartWidget(QWidget):
    """Scatter plot for experiment metrics (e.g. Sharpe vs return)."""

    def __init__(self) -> None:
        super().__init__()
        self._points: list[tuple[float, float, str]] = []
        self._x_label = "Sharpe"
        self._y_label = "Return"
        self.setMinimumHeight(200)
        self.setObjectName("scatter-chart")

    def set_points(
        self,
        points: list[tuple[float, float, str]],
        *,
        x_label: str = "Sharpe",
        y_label: str = "Return",
    ) -> None:
        self._points = list(points)
        self._x_label = x_label
        self._y_label = y_label
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: ARG002
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect()
        pal = chart_palette()
        painter.fillRect(rect, QColor(pal.background))
        if not self._points:
            _paint_empty(painter, rect, "Run experiments to populate scatter")
            return
        xs = [p[0] for p in self._points]
        ys = [p[1] for p in self._points]
        x_lo, x_hi = min(xs), max(xs)
        y_lo, y_hi = min(ys), max(ys)
        if x_lo == x_hi:
            x_lo -= 0.5
            x_hi += 0.5
        if y_lo == y_hi:
            y_lo -= 0.01
            y_hi += 0.01
        pad = 28
        plot = rect.adjusted(pad, pad, -pad, -pad)
        for i, (x, y, _label) in enumerate(self._points):
            px = plot.x() + plot.width() * (x - x_lo) / (x_hi - x_lo)
            py = plot.y() + plot.height() * (1.0 - (y - y_lo) / (y_hi - y_lo))
            color = SERIES_COLORS[i % len(SERIES_COLORS)]
            painter.setBrush(QColor(color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(int(px) - 4, int(py) - 4, 8, 8)
        painter.setPen(QColor(pal.muted))
        font = QFont()
        font.setPointSize(9)
        painter.setFont(font)
        painter.drawText(plot.x(), rect.height() - 6, self._x_label)
        painter.save()
        painter.translate(8, plot.center().y())
        painter.rotate(-90)
        painter.drawText(0, 0, self._y_label)
        painter.restore()


class TargetBarWidget(QWidget):
    """Progress toward a target with optional tick marker (Meridiem-style)."""

    def __init__(self, *, min_height: int = 14) -> None:
        super().__init__()
        self._value: float | None = None
        self._target: float | None = None
        self._higher_is_better = True
        self.setMinimumHeight(min_height)
        self.setMaximumHeight(min_height + 4)

    def set_progress(
        self,
        value: float,
        target: float,
        *,
        higher_is_better: bool = True,
    ) -> None:
        self._value = value
        self._target = target if target else 1.0
        self._higher_is_better = higher_is_better
        self.setVisible(True)
        self.update()

    def clear_progress(self) -> None:
        self._value = None
        self.setVisible(False)
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: ARG002
        if self._value is None or self._target is None:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(0, 4, 0, -4)
        pal = chart_palette()
        painter.fillRect(rect, QColor(pal.grid))
        span = abs(self._target) if self._target else 1.0
        if self._higher_is_better:
            fill_ratio = min(max(self._value / span, 0.0), 1.0) if span else 0.0
            tick_ratio = min(max(self._target / span, 0.0), 1.0) if span else 1.0
            color = "#26a69a" if self._value >= self._target else "#42a5f5"
        else:
            fill_ratio = min(max(self._value / span, 0.0), 1.0) if span else 0.0
            tick_ratio = min(max(self._target / span, 0.0), 1.0) if span else 1.0
            color = "#26a69a" if self._value <= self._target else "#ef5350"
        fill_w = int(rect.width() * fill_ratio)
        if fill_w > 0:
            painter.fillRect(rect.x(), rect.y(), fill_w, rect.height(), QColor(color))
        tick_x = rect.x() + int(rect.width() * tick_ratio)
        painter.setPen(QPen(QColor(pal.foreground), 2))
        painter.drawLine(tick_x, rect.y() - 2, tick_x, rect.y() + rect.height() + 2)


class DonutChartWidget(QWidget):
    """Simple allocation donut for portfolio weights."""

    def __init__(self, *, min_height: int = 160) -> None:
        super().__init__()
        self._slices: list[tuple[str, float, str]] = []
        self.setMinimumHeight(min_height)
        self.setObjectName("donut-chart")

    def set_slices(self, slices: list[tuple[str, float, str]]) -> None:
        """Each slice: (label, weight 0-1, color hex)."""
        self._slices = [(label, weight, color) for label, weight, color in slices if weight > 0]
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: ARG002
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect()
        pal = chart_palette()
        painter.fillRect(rect, QColor(pal.background))
        if not self._slices:
            _paint_empty(painter, rect, "No weights to chart")
            return
        total = sum(w for _, w, _ in self._slices) or 1.0
        size = min(rect.width(), rect.height()) - 24
        cx = rect.center().x()
        cy = rect.center().y()
        outer = size // 2
        inner = int(outer * 0.55)
        start_angle = 90 * 16
        for _label, weight, color in self._slices:
            span = int(360 * 16 * weight / total)
            painter.setBrush(QColor(color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawPie(cx - outer, cy - outer, outer * 2, outer * 2, start_angle, -span)
            start_angle -= span
        painter.setBrush(QColor(pal.background))
        painter.drawEllipse(cx - inner, cy - inner, inner * 2, inner * 2)
        painter.setPen(QColor(pal.muted))
        font = QFont()
        font.setPointSize(9)
        painter.setFont(font)
        y = rect.y() + 8
        for label, weight, color in self._slices[:6]:
            painter.setPen(QColor(color))
            painter.drawText(rect.x() + 8, y, "■")
            painter.setPen(QColor(pal.foreground))
            painter.drawText(rect.x() + 22, y, f"{label[:12]} {100 * weight / total:.0f}%")
            y += 14


class KpiCard(QFrame):
    """Single KPI tile with optional sparkline."""

    def __init__(
        self,
        title: str,
        value: str = "—",
        *,
        accent: str = "#42a5f5",
        subtitle: str = "",
    ) -> None:
        super().__init__()
        self.setObjectName("kpiCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)
        self._title = QLabel(title)
        self._value = QLabel(value)
        self._subtitle = QLabel(subtitle)
        self._target_bar = TargetBarWidget()
        self._target_bar.setVisible(False)
        self._spark = SparklineWidget(min_height=40)
        self._spark.setVisible(False)
        self._sync_theme_colors()
        layout.addWidget(self._title)
        layout.addWidget(self._value)
        layout.addWidget(self._target_bar)
        layout.addWidget(self._subtitle)
        layout.addWidget(self._spark)
        self._value.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {accent};")

    def _sync_theme_colors(self) -> None:
        pal = chart_palette()
        self._title.setStyleSheet(f"color: {pal.muted}; font-size: 11px;")
        self._subtitle.setStyleSheet(f"color: {pal.muted}; font-size: 10px;")

    def showEvent(self, event: QShowEvent) -> None:  # noqa: ARG002
        self._sync_theme_colors()
        super().showEvent(event)

    def set_value(self, value: str, *, accent: str | None = None) -> None:
        self._value.setText(value)
        if accent:
            self._value.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {accent};")

    def set_subtitle(self, text: str) -> None:
        self._subtitle.setText(text)
        self._subtitle.setVisible(bool(text))

    def set_target_progress(
        self,
        value: float,
        target: float,
        *,
        higher_is_better: bool = True,
        headroom_label: str = "",
    ) -> None:
        self._target_bar.set_progress(value, target, higher_is_better=higher_is_better)
        if headroom_label:
            self.set_subtitle(headroom_label)

    def clear_target_progress(self) -> None:
        self._target_bar.clear_progress()

    def set_sparkline(self, values: list[float], *, color: str = SERIES_COLORS[0]) -> None:
        if len(values) >= 2:
            self._spark.set_values(values, color=color)
            self._spark.setVisible(True)
        else:
            self._spark.setVisible(False)


class DashboardStrip(QWidget):
    """Responsive KPI strip that wraps cards instead of shrinking their content."""

    def __init__(self, titles: list[str]) -> None:
        super().__init__()
        self.setObjectName("dashboardStrip")
        self._grid = QGridLayout(self)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setSpacing(8)
        self._cards: list[KpiCard] = []
        self._columns = 0
        for title in titles:
            card = KpiCard(title)
            card.setMinimumWidth(180)
            self._cards.append(card)
        self._reflow(columns=len(titles))

    def card(self, index: int) -> KpiCard:
        return self._cards[index]

    @property
    def cards(self) -> list[KpiCard]:
        return list(self._cards)

    def apply_responsive_state(self, state: ResponsiveState) -> None:
        self._reflow(columns=min(len(self._cards), state.kpi_columns))

    def resizeEvent(self, event: object) -> None:  # noqa: N802
        state = responsive_state(self.width(), self.height())
        self.apply_responsive_state(state)
        super().resizeEvent(event)  # type: ignore[arg-type]

    def _reflow(self, *, columns: int) -> None:
        columns = max(1, min(columns, len(self._cards)))
        if columns == self._columns:
            return
        self._columns = columns
        while self._grid.count():
            self._grid.takeAt(0)
        for index, card in enumerate(self._cards):
            self._grid.addWidget(card, index // columns, index % columns)
        for column in range(columns):
            self._grid.setColumnStretch(column, 1)


class LogTimelineWidget(QWidget):
    """Mini timeline of log severity buckets (newest on the right)."""

    def __init__(self) -> None:
        super().__init__()
        self._counts: list[tuple[str, int]] = []
        self.setMinimumHeight(48)
        self.setObjectName("log-timeline")

    def set_counts(self, counts: list[tuple[str, int]]) -> None:
        self._counts = list(counts)
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: ARG002
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect()
        pal = chart_palette()
        painter.fillRect(rect, QColor(pal.background))
        if not self._counts:
            _paint_empty(painter, rect, "No log events yet")
            return
        colors = {
            "error": "#ef5350",
            "warning": "#ffa726",
            "info": "#42a5f5",
            "debug": "#78909c",
        }
        max_count = max(count for _, count in self._counts) or 1
        bar_w = max((rect.width() - 16) // max(len(self._counts), 1), 6)
        x = 8
        base_y = rect.height() - 8
        for level, count in self._counts:
            height = int((rect.height() - 20) * count / max_count)
            color = colors.get(level, pal.muted)
            painter.fillRect(x, base_y - height, bar_w - 2, height, QColor(color))
            painter.setPen(QColor(pal.muted))
            font = QFont()
            font.setPointSize(8)
            painter.setFont(font)
            painter.drawText(x, rect.height() - 1, level[:1].upper())
            x += bar_w


class GraphPreviewWidget(QWidget):
    """Compact node-link preview for knowledge graph edges."""

    def __init__(self) -> None:
        super().__init__()
        self._edges: list[tuple[str, str, str]] = []
        self.setMinimumHeight(160)
        self.setObjectName("graph-preview")

    def set_edges(self, edges: list[tuple[str, str, str]]) -> None:
        self._edges = list(edges[:24])
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: ARG002
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect()
        pal = chart_palette()
        painter.fillRect(rect, QColor(pal.background))
        if not self._edges:
            _paint_empty(painter, rect, "No graph edges match filters")
            return
        nodes: list[str] = []
        for src, _rel, tgt in self._edges:
            for node in (src, tgt):
                if node not in nodes:
                    nodes.append(node)
        node_count = max(len(nodes), 1)
        positions: dict[str, tuple[int, int]] = {}
        left_x = rect.x() + 24
        right_x = rect.x() + rect.width() - 24
        mid_y = rect.center().y()
        for i, node in enumerate(nodes[:12]):
            t = i / max(min(node_count, 12) - 1, 1)
            x = int(left_x + (right_x - left_x) * t)
            y = int(mid_y + (i % 3 - 1) * 28)
            positions[node] = (x, y)
        painter.setPen(QPen(QColor(pal.grid), 1))
        for src, rel, tgt in self._edges[:24]:
            if src not in positions or tgt not in positions:
                continue
            sx, sy = positions[src]
            tx, ty = positions[tgt]
            painter.drawLine(sx, sy, tx, ty)
            mx, my = (sx + tx) // 2, (sy + ty) // 2
            painter.setPen(QColor(pal.muted))
            font = QFont()
            font.setPointSize(7)
            painter.setFont(font)
            painter.drawText(mx - 16, my - 4, rel[:10])
            painter.setPen(QPen(QColor(pal.grid), 1))
        for node, (x, y) in positions.items():
            painter.setBrush(QColor(SERIES_COLORS[len(positions) % len(SERIES_COLORS)]))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(x - 5, y - 5, 10, 10)
            painter.setPen(QColor(pal.foreground))
            font = QFont()
            font.setPointSize(8)
            painter.setFont(font)
            short = node.split(":")[-1][:10]
            painter.drawText(x - 24, y + 16, short)
