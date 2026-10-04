"""The backtest timeline is an exchange/session timeline, not a name intersection."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from quantlab.backtest.engine import shared_calendar
from quantlab.core.identifiers import InstrumentId
from quantlab.core.time import PointInTime
from quantlab.domain.models import OHLCVBar


def _bar(symbol: str, when: datetime) -> OHLCVBar:
    return OHLCVBar(
        instrument=InstrumentId.parse(f"NSE:{symbol}"),
        pit=PointInTime(
            event_time=when,
            effective_time=when,
            available_time=when,
            ingestion_time=when,
        ),
        open=100.0,
        high=101.0,
        low=99.0,
        close=100.0,
    )


def test_missing_security_bar_does_not_delete_exchange_session() -> None:
    day = datetime(2024, 1, 2, tzinfo=UTC)
    next_day = day + timedelta(days=1)
    calendar = shared_calendar(
        {
            InstrumentId.parse("NSE:AAA"): [_bar("AAA", day), _bar("AAA", next_day)],
            # IPO/suspension/data gap: this name has no print on the second session.
            InstrumentId.parse("NSE:BBB"): [_bar("BBB", day)],
        }
    )
    assert calendar == [day, next_day]
