from __future__ import annotations

from contextlib import suppress
from datetime import UTC, datetime, timedelta
from threading import Event, get_ident

import pytest

from quantlab.app.live_market import LiveMarketFeed
from quantlab.realtime_data.errors import RealTimeDataError
from quantlab.realtime_data.freeze import freeze
from quantlab.realtime_data.models import MarketObservation, QualityStatus, RealTimeSnapshot

NOW = datetime(2026, 10, 7, 4, 0, tzinfo=UTC)


def quote_snapshot(when: datetime = NOW) -> RealTimeSnapshot:
    row = MarketObservation(
        observation_id="quote-infy",
        security_id="NSE:INFY",
        venue="NSE",
        source="kite-rest-quote-v3",
        event_time=when,
        exchange_time=when,
        source_time=when,
        receive_time=when,
        processing_time=when,
        price=1021.5,
        volume=0,
        provenance="kite-rest-quote-v3",
        payload_hash=when.isoformat(),
        quality=QualityStatus.VALID,
    )
    return freeze(
        (row,),
        as_of=when,
        source_manifest="production-observe-only:kite-rest-quote-v3",
        provenance={
            "active_source": "kite-rest-quote-v3",
            "configured_instruments": ["NSE:INFY", "NSE:TCS"],
            "max_quote_age_seconds": 5.0,
        },
    )


def complete(feed: LiveMarketFeed) -> None:
    assert feed._future is not None
    # Errors must be consumed/redacted by tick, not by this synchronization helper.
    with suppress(Exception):
        feed._future.result(timeout=2)
    feed.tick()


def test_no_implicit_network_on_construction() -> None:
    calls: list[int] = []
    feed = LiveMarketFeed(fetch=lambda: calls.append(1) or quote_snapshot())
    try:
        feed.tick()
        assert not calls and feed.status == "DISCONNECTED"
    finally:
        feed.close()


def test_background_single_flight_and_request_cadence() -> None:
    entered, release = Event(), Event()
    threads: list[int] = []
    timer = [0.0]

    def fetch() -> RealTimeSnapshot:
        threads.append(get_ident())
        entered.set()
        assert release.wait(2)
        return quote_snapshot()

    feed = LiveMarketFeed(fetch=fetch, timer=lambda: timer[0], clock=lambda: NOW)
    try:
        feed.start()
        assert entered.wait(1)
        assert threads[0] != get_ident()
        for _ in range(10):
            feed.refresh_now()
        assert len(threads) == 1 and feed.status == "CONNECTING"
        release.set()
        complete(feed)
        feed.tick()
        assert len(threads) == 1
        timer[0] = 2
        feed.tick()
        complete(feed)
        assert len(threads) == 2
    finally:
        release.set()
        feed.close()


def test_missing_instruments_zero_volume_and_quote_aging() -> None:
    now = [NOW]
    feed = LiveMarketFeed(fetch=quote_snapshot, timer=lambda: 0, clock=lambda: now[0])
    try:
        feed.start()
        complete(feed)
        rows = feed.quote_rows()
        assert rows[0]["price"] == 1021.5 and rows[0]["volume"] == 0
        assert rows[0]["bid"] is None
        assert rows[1]["price"] is None and rows[1]["quality"] == "missing"
        assert feed.status == "DEGRADED"
        now[0] += timedelta(seconds=6)
        assert feed.quote_rows()[0]["quality"] == "stale"
        assert feed.quote_rows()[0]["age_seconds"] == 6
        assert feed.status == "STALE"
    finally:
        feed.close()


def test_pause_discards_late_result_and_close_prevents_requests() -> None:
    release = Event()

    def fetch() -> RealTimeSnapshot:
        assert release.wait(2)
        return quote_snapshot()

    feed = LiveMarketFeed(fetch=fetch, timer=lambda: 0)
    try:
        feed.start()
        feed.pause()
        release.set()
        complete(feed)
        assert feed.snapshot is None and not feed.enabled
        feed.close()
        feed.start()
        assert feed._future is None
    finally:
        release.set()
        feed.close()


def test_auth_failure_stops_and_reconnect_loads_new_result() -> None:
    count = [0]
    timer = [0.0]

    def fetch() -> RealTimeSnapshot:
        count[0] += 1
        if count[0] == 1:
            raise RealTimeDataError("Kite quote authentication rejected")
        return quote_snapshot()

    feed = LiveMarketFeed(fetch=fetch, timer=lambda: timer[0], clock=lambda: NOW)
    try:
        feed.start()
        complete(feed)
        assert feed.status == "AUTH REQUIRED" and not feed.enabled
        timer[0] = 100
        feed.tick()
        assert count[0] == 1
        feed.start()
        complete(feed)
        assert feed.error is None and feed.snapshot is not None
    finally:
        feed.close()


def test_failure_retains_prices_as_unavailable_and_backs_off() -> None:
    count = [0]
    timer = [0.0]

    def fetch() -> RealTimeSnapshot:
        count[0] += 1
        if count[0] > 1:
            raise RealTimeDataError("Kite quote request failed (429)")
        return quote_snapshot()

    feed = LiveMarketFeed(fetch=fetch, timer=lambda: timer[0], clock=lambda: NOW)
    try:
        feed.start()
        complete(feed)
        timer[0] = 2
        feed.tick()
        complete(feed)
        assert feed.status == "ERROR"
        assert feed.quote_rows()[0]["price"] == 1021.5
        assert feed.quote_rows()[0]["quality"] == "unavailable"
        timer[0] = 4
        feed.tick()
        assert count[0] == 2
        timer[0] = 6
        feed.tick()
        complete(feed)
        assert count[0] == 3
    finally:
        feed.close()


def test_unexpected_exception_does_not_expose_secrets() -> None:
    def fetch() -> RealTimeSnapshot:
        raise ValueError("secret-key-and-token-in-an-unexpected-error")

    feed = LiveMarketFeed(fetch=fetch, timer=lambda: 0)
    try:
        feed.start()
        complete(feed)
        assert feed.status == "ERROR"
        assert feed.error is not None and "secret-key" not in feed.error
    finally:
        feed.close()


def test_history_bounded_deduplicated_and_split_after_pause() -> None:
    now = [NOW]
    timer = [0.0]
    feed = LiveMarketFeed(
        fetch=lambda: quote_snapshot(now[0]),
        clock=lambda: now[0],
        timer=lambda: timer[0],
        history_limit=2,
    )
    try:
        feed.start()
        complete(feed)
        timer[0] = 2
        feed.tick()
        complete(feed)
        assert len(feed.history("NSE:INFY")) == 1
        for index in (2, 3):
            timer[0] = index * 2
            now[0] += timedelta(seconds=2)
            feed.tick()
            complete(feed)
        assert len(feed.history("NSE:INFY")) == 2
        feed.pause()
        timer[0] += 2
        now[0] += timedelta(seconds=2)
        feed.start()
        complete(feed)
        history = feed.history("NSE:INFY")
        assert history[0].segment != history[1].segment
    finally:
        feed.close()


def test_non_kite_data_cannot_enter_live_workspace() -> None:
    fake = quote_snapshot().model_copy(update={"extras": {"active_source": "mock"}})
    feed = LiveMarketFeed(fetch=lambda: fake, timer=lambda: 0)
    try:
        feed.start()
        complete(feed)
        assert feed.snapshot is None and feed.status == "ERROR"
    finally:
        feed.close()


def test_invalid_poll_interval_rejected() -> None:
    with pytest.raises(ValueError):
        LiveMarketFeed(interval_seconds=0.1)
