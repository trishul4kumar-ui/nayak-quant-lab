from __future__ import annotations

import csv
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtGui import QWheelEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from quantlab.app.bootstrap import bootstrap
from quantlab.app.chart_history import ChartDataSession
from quantlab.app.live_market import QuotePoint
from quantlab.app.settings_store import ExperienceMode, UiTheme
from quantlab.realtime_data.candles import Candle, CandleSeries, ChartRequest
from quantlab.ui.pages.market import MarketPage
from quantlab.ui.theme import apply_theme
from quantlab.ui.widgets.interactive_chart import InteractivePriceChart
from quantlab.ui.widgets.market_chart import MarketChartWorkspace

NOW = datetime(2026, 10, 7, 4, 30, tzinfo=UTC)


@pytest.fixture
def qapp() -> QApplication:
    app = QApplication.instance()
    return app if isinstance(app, QApplication) else QApplication([])


def series(request: ChartRequest | None = None) -> CandleSeries:
    request = request or ChartRequest("NSE:INFY")
    bars = tuple(
        Candle(
            NOW - timedelta(minutes=70 - i),
            100 + i / 10,
            101 + i / 10,
            99 + i / 10,
            100.5 + i / 10,
            100 + i,
        )
        for i in range(70)
    )
    return CandleSeries(request, bars, NOW)


def test_canvas_inspection_navigation_keyboard_and_drawings(qapp: QApplication) -> None:
    chart = InteractivePriceChart()
    chart.set_series("NSE:INFY", series())
    chart.resize(1000, 600)
    chart.show()
    qapp.processEvents()
    try:
        assert not chart.grab().isNull()
        assert "O 100.00" in chart.inspection(0)
        assert "Vol 100" in chart.inspection(0)
        before = chart._span
        chart.zoom(0.8)
        assert chart._span < before and not chart.follow
        chart.fit()
        assert chart._start < 0
        chart.latest()
        assert chart.follow
        wheel = QWheelEvent(
            QPointF(220, 120),
            QPointF(220, 120),
            QPoint(),
            QPoint(0, 120),
            Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier,
            Qt.ScrollPhase.NoScrollPhase,
            False,
        )
        qapp.sendEvent(chart, wheel)
        assert not chart.follow and chart._span < before
        start = chart._start
        QTest.mousePress(chart, Qt.MouseButton.LeftButton, pos=QPoint(220, 120))
        QTest.mouseMove(chart, QPoint(300, 120))
        QTest.mouseRelease(chart, Qt.MouseButton.LeftButton, pos=QPoint(300, 120))
        assert chart._start < start and chart._drag is None
        chart.tool = "Horizontal"
        point = QPoint(220, 120)
        QTest.mouseClick(chart, Qt.MouseButton.LeftButton, pos=point)
        assert len(chart.drawings) == 1
        chart.tool = "Trend line"
        QTest.mouseClick(chart, Qt.MouseButton.LeftButton, pos=point)
        QTest.mouseClick(chart, Qt.MouseButton.LeftButton, pos=QPoint(420, 160))
        assert len(chart.drawings) == 2
        QTest.keyClick(chart, Qt.Key.Key_Left)
        assert chart._hover is not None
        chart.set_series("BSE:HAL", series(ChartRequest("BSE:HAL")))
        assert not chart.drawings
        for view in ("Candles", "OHLC", "Line", "Area"):
            chart.view = view
            chart.indicators = {"SMA 20", "EMA 9", "EMA 26", "BB 20", "RSI 14"}
            chart.update()
            qapp.processEvents()
            assert not chart.grab().isNull()
    finally:
        chart.close()


def test_workspace_timeframes_observed_mode_expand_and_source_csv(
    qapp: QApplication,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime = bootstrap(data_dir=tmp_path / "runtime")
    runtime.chart_data.close()
    runtime.chart_data = ChartDataSession(fetch=series)
    runtime.live_market.enabled = True
    widget = MarketChartWorkspace(runtime)
    widget.resize(1000, 700)
    widget.show()
    qapp.processEvents()
    try:
        widget.set_instrument(
            "NSE:INFY",
            quote={"price": 101, "quality": "valid", "quote_time": NOW},
            observed=[QuotePoint(NOW, 101, 0)],
        )
        assert runtime.chart_data._future is not None
        runtime.chart_data._future.result(timeout=2)
        widget._poll()
        assert widget._canvas.series and "70 bars" in widget._status.text()
        widget._view.setCurrentText("OHLC")
        assert widget._canvas.view == "OHLC"
        before = widget._canvas._span
        widget._zoom_in.click()
        assert widget._canvas._span < before and not widget._follow.isChecked()
        widget._fit.click()
        assert widget._canvas._start < 0
        widget._follow.click()
        assert widget._canvas.follow and widget._follow.isChecked()
        widget._indicator_actions["RSI 14"].setChecked(True)
        assert "RSI 14" in widget._canvas.indicators
        qapp.processEvents()
        widget._tool.setCurrentText("Horizontal")
        QTest.mouseClick(widget._canvas, Qt.MouseButton.LeftButton, pos=QPoint(220, 120))
        assert len(widget._canvas.drawings) == 1
        widget._undo.click()
        assert not widget._canvas.drawings
        QTest.mouseClick(widget._canvas, Qt.MouseButton.LeftButton, pos=QPoint(220, 120))
        widget._clear.click()
        assert not widget._canvas.drawings
        png_path = tmp_path / "chart.png"
        monkeypatch.setattr(
            "quantlab.ui.widgets.market_chart.QFileDialog.getSaveFileName",
            lambda *a: (str(png_path), "PNG"),
        )
        widget._png.click()
        assert png_path.read_bytes().startswith(b"\x89PNG")
        csv_path = tmp_path / "candles.csv"
        monkeypatch.setattr(
            "quantlab.ui.widgets.market_chart.QFileDialog.getSaveFileName",
            lambda *a: (str(csv_path), "CSV"),
        )
        widget._export_csv()
        with csv_path.open() as stream:
            rows = list(csv.reader(stream))
        assert len(rows) == 71 and rows[1][0] == "kite-historical-v3"
        assert rows[1][5:9] == ["100.0", "101.0", "99.0", "100.5"]
        widget._expand.click()
        assert widget._expanded and widget.parent() is widget._expanded
        assert widget._canvas.parent() is widget
        widget._view.setCurrentText("Area")
        assert widget._canvas.view == "Area"
        widget._expanded.close()
        qapp.processEvents()
        assert widget._expanded is None and widget._canvas.parent() is widget
        widget._timeframe.setCurrentIndex(widget._timeframe.findData("day"))
        widget._range.setCurrentIndex(3)
        assert runtime.chart_data.request == ChartRequest("NSE:INFY", "day", 366)
        widget._timeframe.setCurrentIndex(0)
        assert runtime.chart_data.request == ChartRequest("NSE:INFY", "minute", 31)
        widget._timeframe.setCurrentIndex(widget._timeframe.findData("observed"))
        assert not widget._indicators.isEnabled()
        assert not widget._auto.isEnabled()
        assert "candle indicators unavailable" in widget._legend.text()
        assert widget._view.currentText() == "Area"  # valid quote view survives the switch
        assert widget._canvas.series is None and len(widget._canvas.samples) == 1
        widget._view.setCurrentText("Candles")
        assert widget._view.currentText() == "Line"
        quote_reloads: list[bool] = []
        monkeypatch.setattr(runtime.live_market, "refresh_now", lambda: quote_reloads.append(True))
        widget._refresh.click()
        assert quote_reloads == [True]
        assert not widget._undo.isEnabled() and not widget._clear.isEnabled()
        widget._export_csv()
        with csv_path.open() as stream:
            rows = list(csv.reader(stream))
        assert rows[1][0] == "kite-rest-quote-v3"
        assert rows[1][3] == "101"
        widget.resize(450, 700)
        qapp.processEvents()
        assert widget._columns == 1 and widget.width() == 450
        assert not widget.grab().isNull()
    finally:
        widget.close()
        runtime.shutdown()


@pytest.mark.parametrize("mode", [ExperienceMode.GUIDED, ExperienceMode.FULL])
def test_themed_market_panel_wrapped_readout_never_overlaps_chart(
    mode: ExperienceMode, qapp: QApplication, tmp_path: Path
) -> None:
    runtime = bootstrap(data_dir=tmp_path)
    runtime.ui_settings.current.experience_mode = mode
    apply_theme(qapp, UiTheme.DARK)
    page = MarketPage(runtime)
    try:
        page.resize(1536, 1040)
        page.show()
        chart = page._price_spark
        chart._canvas.set_series("NSE:INFY", series())
        chart._readout.setText(chart._canvas.inspection(69) + " · forming / may revise")
        chart._status.setText(
            "kite-historical-v3 · 70 bars · fetched 07 Oct 10:00:00 IST · latest candle may "
            "revise · trading-bar axis (closed-session gaps compressed)"
        )
        for _ in range(3):
            qapp.processEvents()
        assert chart._canvas.geometry().bottom() < chart._status.y()
        assert chart.height() >= chart._root.minimumHeightForWidth(chart.width())
    finally:
        page.close()
        page.deleteLater()
        runtime.shutdown()
