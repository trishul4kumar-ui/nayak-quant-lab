from __future__ import annotations

from concurrent.futures import Future
from datetime import UTC, datetime

from quantlab.app.chart_history import ChartDataSession
from quantlab.app.chart_indicators import bollinger, ema, rsi, sma
from quantlab.realtime_data.candles import CandleSeries, ChartRequest
from quantlab.realtime_data.errors import RealTimeDataError

NOW = datetime(2026, 10, 7, 4, 30, tzinfo=UTC)


def test_indicators_known_values_warmup_and_flat_rsi() -> None:
    values = [float(i) for i in range(1, 41)]
    assert sma(values, 20)[:19] == [None] * 19
    assert sma(values, 20)[19] == 10.5
    assert ema(values, 9)[8] == 5
    assert ema(values, 9)[9] == 6
    assert rsi(values)[:14] == [None] * 14
    assert rsi(values)[14:] == [100] * 26
    assert rsi(list(reversed(values)))[14:] == [0] * 26
    assert rsi([2.0] * 40)[14:] == [50] * 26
    assert bollinger([2.0] * 40)[0][19:] == [2] * 21


def test_loader_no_implicit_requests_cadence_pause_and_manual_auto_off_reload() -> None:
    timer = [0.0]
    calls: list[ChartRequest] = []
    session = ChartDataSession(
        fetch=lambda r: calls.append(r) or CandleSeries(r, (), NOW), timer=lambda: timer[0]
    )
    try:
        session.tick(enabled=True)
        assert not calls
        session.select(ChartRequest("NSE:INFY"))
        session.tick(enabled=False)
        assert not calls
        session.tick(enabled=True)
        assert session._future
        session._future.result(timeout=2)
        session.tick(enabled=True)
        assert len(calls) == 1 and session.series
        timer[0] = 30
        session.tick(enabled=True, auto_refresh=False)
        assert len(calls) == 1
        session.refresh()
        session.tick(enabled=True, auto_refresh=False)
        assert session._future
        session._future.result(timeout=2)
        session.tick(enabled=False)
        assert len(calls) == 2
    finally:
        session.close()


def test_old_selection_result_is_discarded_and_unknown_exceptions_are_redacted() -> None:
    session = ChartDataSession()
    try:
        old = ChartRequest("NSE:INFY")
        session.select(ChartRequest("NSE:TCS"))
        future: Future[CandleSeries] = Future()
        future.set_result(CandleSeries(old, (), NOW))
        session._future, session._submitted = future, old
        session.tick(enabled=False)
        assert session.series is None
        future = Future()
        future.set_exception(ValueError("secret-access-token"))
        session._future, session._submitted = future, session.request
        session.tick(enabled=False)
        assert session.error and "secret" not in session.error
        future = Future()
        future.set_exception(RealTimeDataError("Kite chart authentication rejected"))
        session._future, session._submitted = future, session.request
        session.tick(enabled=False)
        assert session._auth_blocked
        session.refresh()
        assert not session._auth_blocked
    finally:
        session.close()
