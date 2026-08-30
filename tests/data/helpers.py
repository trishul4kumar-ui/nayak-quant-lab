"""Shared constructors for fabric tests. Labeled synthetic — not NSE prints."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from quantlab.core.identifiers import InstrumentId
from quantlab.core.time import PointInTime
from quantlab.data.fabric.types import DataKind, PriceKind
from quantlab.domain.models import BarInterval, OHLCVBar


def utc_day(year: int, month: int, day: int, hour: int = 10) -> datetime:
    return datetime(year, month, day, hour, 0, tzinfo=UTC)


def make_bar(
    symbol: str,
    when: datetime,
    *,
    close: float = 100.0,
    available: datetime | None = None,
    volume: float = 1_000.0,
    exchange: str = "NSE",
) -> OHLCVBar:
    available_time = available if available is not None else when
    open_px = close
    high = close * 1.01
    low = close * 0.99
    return OHLCVBar(
        instrument=InstrumentId(exchange=exchange, symbol=symbol),
        pit=PointInTime(
            event_time=when,
            effective_time=when,
            available_time=available_time,
            ingestion_time=available_time,
        ),
        interval=BarInterval.DAY,
        open=open_px,
        high=high,
        low=low,
        close=close,
        volume=volume,
        dataset_version="test",
        source_id="test_fixture",
        session_date=when.date().isoformat(),
        price_kind=PriceKind.RAW_PRICE.value,
        data_kind=DataKind.SYNTHETIC.value,
    )


def weekday_series(
    symbol: str,
    start: datetime,
    n: int,
    *,
    start_px: float = 100.0,
    delay: timedelta | None = None,
) -> list[OHLCVBar]:
    bars: list[OHLCVBar] = []
    price = start_px
    cursor = start
    while len(bars) < n:
        if cursor.weekday() < 5:
            available = cursor if delay is None else cursor + delay
            bars.append(make_bar(symbol, cursor, close=price, available=available))
            price *= 1.001
        cursor += timedelta(days=1)
    return bars
