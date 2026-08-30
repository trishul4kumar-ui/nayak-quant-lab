"""Dashboard chart widget smoke tests."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication

from quantlab.math.drawdown import drawdown_series
from quantlab.ui.widgets.charts import (
    BarChartWidget,
    ChartSeries,
    DashboardStrip,
    DrawdownChartWidget,
    KpiCard,
    MultiSeriesChartWidget,
    ScatterChartWidget,
    SparklineWidget,
)


@pytest.fixture
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_sparkline_paints(qapp: QApplication) -> None:
    w = SparklineWidget()
    w.set_values([100.0, 102.0, 101.0, 105.0])
    w.show()
    qapp.processEvents()
    w.repaint()
    qapp.processEvents()


def test_multi_series_chart(qapp: QApplication) -> None:
    w = MultiSeriesChartWidget()
    w.set_series(
        [
            ChartSeries("A", [1.0, 2.0, 1.5], color="#42a5f5"),
            ChartSeries("B", [1.0, 1.2, 1.8], color="#66bb6a"),
        ]
    )
    w.show()
    qapp.processEvents()


def test_drawdown_chart(qapp: QApplication) -> None:
    equity = [100.0, 110.0, 95.0, 105.0]
    w = DrawdownChartWidget()
    w.set_drawdown(drawdown_series(equity))
    w.show()
    qapp.processEvents()


def test_bar_and_scatter(qapp: QApplication) -> None:
    bar = BarChartWidget()
    bar.set_items([("Sharpe", 1.2, "#42a5f5"), ("Net", 0.05, "#66bb6a")])
    bar.show()
    scatter = ScatterChartWidget()
    scatter.set_points([(0.5, 0.02, "run-a"), (1.1, 0.08, "run-b")])
    scatter.show()
    qapp.processEvents()


def test_dashboard_strip(qapp: QApplication) -> None:
    strip = DashboardStrip(["A", "B"])
    strip.card(0).set_value("1.23")
    strip.show()
    qapp.processEvents()


def test_kpi_card_sparkline(qapp: QApplication) -> None:
    card = KpiCard("Sharpe", "1.05")
    card.set_sparkline([1.0, 1.02, 1.05])
    card.show()
    qapp.processEvents()
