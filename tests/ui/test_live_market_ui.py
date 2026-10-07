from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication, QLabel

from quantlab.app.bootstrap import bootstrap
from quantlab.app.chart_history import ChartDataSession
from quantlab.app.live_market import LiveMarketFeed
from quantlab.realtime_data.candles import CandleSeries
from quantlab.realtime_data.freeze import freeze
from quantlab.realtime_data.models import MarketObservation, QualityStatus
from quantlab.ui.pages.market import MarketPage
from quantlab.ui.pages.realtime_data_lab import RealTimeDataLabPage
from quantlab.ui.widgets.footer_status import FooterStatusBar

NOW = datetime(2026, 10, 7, 4, 0, tzinfo=UTC)


@pytest.fixture
def qapp() -> QApplication:
    app = QApplication.instance()
    return app if isinstance(app, QApplication) else QApplication([])


def test_live_controls_selection_pause_and_footer(
    tmp_path: Path,
    qapp: QApplication,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rows = tuple(
        MarketObservation(
            observation_id=symbol,
            security_id=symbol,
            venue="NSE",
            source="kite-rest-quote-v3",
            event_time=NOW,
            exchange_time=NOW,
            source_time=NOW,
            receive_time=NOW,
            processing_time=NOW,
            price=price,
            volume=0,
            payload_hash=symbol,
            provenance="kite-rest-quote-v3",
            quality=QualityStatus.VALID,
        )
        for symbol, price in (("NSE:INFY", 1021.5), ("NSE:TCS", 2089.4))
    )
    frozen = freeze(
        rows,
        as_of=NOW,
        source_manifest="production-observe-only:kite-rest-quote-v3",
        provenance={"active_source": "kite-rest-quote-v3", "coverage": 1.0},
    )
    runtime = bootstrap(data_dir=tmp_path)
    runtime.chart_data.close()
    runtime.chart_data = ChartDataSession(fetch=lambda request: CandleSeries(request, (), NOW))
    runtime.live_market.close()
    timer = [0.0]
    runtime.live_market = LiveMarketFeed(
        fetch=lambda: frozen, clock=lambda: NOW, timer=lambda: timer[0]
    )
    captures: list[str] = []
    monkeypatch.setattr(
        "quantlab.ui.pages.realtime_data_lab.record_snapshot_payload",
        lambda item: captures.append(item.snapshot_id),
    )
    page = MarketPage(runtime)
    diagnostics = RealTimeDataLabPage(runtime)
    try:
        assert page._watchlist.rowCount() == 0
        assert page._detail.item(0, 1).text() == "No Kite quotes yet"
        page._connect.click()
        assert runtime.live_market._future is not None
        runtime.live_market._future.result(timeout=2)
        runtime.live_market.tick()
        page.refresh()
        assert page._feed_state.text() == "Kite · LIVE QUOTES"
        assert page._watchlist.rowCount() == 2
        assert page._watchlist.item(0, 1).text() == "1,021.50"
        assert page._watchlist.horizontalHeaderItem(1).text() == "LTP / value"
        assert "provider units" in page._detail.item(1, 0).text()
        assert page._watchlist.item(0, 2).text() == "—"
        assert page._watchlist.item(0, 4).text() == "0"
        assert "IST" in page._watchlist.item(0, 5).text()
        page._watchlist.selectRow(1)
        page._watchlist._on_cell(1, 0)
        price_cell = page._watchlist.item(0, 1)
        page._watchlist.setColumnWidth(1, 177)
        page.refresh()
        assert page._watchlist.item(0, 1) is price_cell
        assert page._watchlist.columnWidth(1) == 177
        assert page._detail.item(0, 1).text() == "NSE:TCS"
        assert page._price_spark._instrument == "NSE:TCS"
        assert "provider units" in page._price_spark.accessibleName()
        diagnostics.refresh()
        assert diagnostics._kite_state.text() == "Kite · LIVE QUOTES"
        footer = FooterStatusBar()
        footer.update_from_runtime(runtime, mode_label="FULL LAB")
        assert "KITE DATA: LIVE QUOTES" in [x.text() for x in footer.findChildren(QLabel)]
        chip = footer._chips["KITE DATA"]
        footer.update_from_runtime(runtime, mode_label="FULL LAB")
        assert footer._chips["KITE DATA"] is chip
        diagnostics._kite_capture.click()
        timer[0] = 2
        runtime.live_market.tick()
        assert runtime.live_market._future is not None
        runtime.live_market._future.result(timeout=2)
        diagnostics._poll()
        assert captures == [frozen.snapshot_id]
        page.show()
        qapp.processEvents()
        chart = page._price_spark
        assert chart._canvas.geometry().bottom() < chart._status.y()
        assert not page.grab().isNull()
        chart._expand.click()
        page.hide()
        runtime.live_market._clock = lambda: NOW + timedelta(seconds=10)
        page._poll_feed()
        assert chart.is_expanded and chart._quote["quality"] == "stale"
        chart._expand.click()
        assert not chart.is_expanded
        page._pause.click()
        assert runtime.live_market.status == "PAUSED"
        assert page._watchlist.item(0, 6).text().endswith("paused")
        assert runtime.gates.live_trading is False and runtime.gates.broker_write_enabled is False
    finally:
        page.close()
        diagnostics.close()
        runtime.shutdown()
