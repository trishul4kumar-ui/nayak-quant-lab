"""Deterministic mock adapter. Not a live feed. Not a broker."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from quantlab.core.identifiers import InstrumentId
from quantlab.realtime_data.hashing import iso, sha256
from quantlab.realtime_data.models import (
    CorrectionStatus,
    MarketObservation,
    MockFeedScenario,
    QualityStatus,
)

SEED_AS_OF = datetime(2024, 1, 2, 4, 0, tzinfo=UTC)
_NAMES = ("TCS", "INFY")


class MockMarketDataAdapter:
    source_id = "mock-observe-only"
    write_enabled = False

    def __init__(self, scenario: MockFeedScenario = MockFeedScenario.NORMAL) -> None:
        self.scenario = scenario
        self._connected = False
        self._cursor = 0

    def connect(self) -> None:
        self._connected = True
        self._cursor = 0

    def disconnect(self) -> None:
        self._connected = False

    def poll(self) -> tuple[MarketObservation, ...]:
        if not self._connected or self.scenario is MockFeedScenario.DISCONNECT:
            return ()
        rows = _seed_rows(self.scenario)
        if self._cursor >= len(rows):
            return ()
        batch = rows[self._cursor :]
        self._cursor = len(rows)
        return batch


def seed_observations(
    scenario: MockFeedScenario = MockFeedScenario.NORMAL,
) -> tuple[MarketObservation, ...]:
    return _seed_rows(scenario)


def _seed_rows(scenario: MockFeedScenario) -> tuple[MarketObservation, ...]:
    if scenario is MockFeedScenario.MALFORMED:
        return (_observation("TCS", 1, None, SEED_AS_OF, QualityStatus.INVALID),)
    if scenario is MockFeedScenario.STALE:
        stale_recv = SEED_AS_OF - timedelta(seconds=30)
        return (
            _observation("TCS", 1, 3500.0, SEED_AS_OF, QualityStatus.STALE, receive=stale_recv),
            _observation("INFY", 2, 1500.0, SEED_AS_OF, QualityStatus.STALE, receive=stale_recv),
        )
    if scenario is MockFeedScenario.GAP:
        return (
            _observation("TCS", 1, 3500.0, SEED_AS_OF, QualityStatus.VALID),
            _observation(
                "INFY",
                3,
                1500.0,
                SEED_AS_OF + timedelta(seconds=1),
                QualityStatus.DEGRADED,
            ),
        )
    if scenario is MockFeedScenario.DUPLICATE:
        first = _observation("TCS", 1, 3500.0, SEED_AS_OF, QualityStatus.VALID)
        dup = _observation("TCS", 1, 3500.0, SEED_AS_OF, QualityStatus.DEGRADED)
        return (first, dup)
    if scenario is MockFeedScenario.OUT_OF_ORDER:
        return (
            _observation("TCS", 2, 3501.0, SEED_AS_OF + timedelta(seconds=1), QualityStatus.VALID),
            _observation("INFY", 1, 1500.0, SEED_AS_OF, QualityStatus.DEGRADED),
        )
    if scenario is MockFeedScenario.CLOCK_DRIFT:
        future = SEED_AS_OF + timedelta(hours=2)
        return (_observation("TCS", 1, 3500.0, future, QualityStatus.DEGRADED, receive=SEED_AS_OF),)
    rows: list[MarketObservation] = []
    seq = 1
    for symbol in _NAMES:
        price = 3500.0 if symbol == "TCS" else 1500.0
        rows.append(_observation(symbol, seq, price, SEED_AS_OF, QualityStatus.VALID))
        seq += 1
    return tuple(rows)


def _observation(
    symbol: str,
    sequence: int,
    price: float | None,
    event_time: datetime,
    quality: QualityStatus,
    *,
    receive: datetime | None = None,
) -> MarketObservation:
    identity = InstrumentId(exchange="NSE", symbol=symbol)
    receive_time = receive or event_time
    payload = {
        "security_id": str(identity),
        "sequence": sequence,
        "price": price,
        "event_time": iso(event_time),
        "source": "mock-observe-only",
    }
    return MarketObservation(
        observation_id=f"obs-{symbol}-{sequence}",
        security_id=str(identity),
        venue="NSE",
        source="mock-observe-only",
        event_time=event_time,
        exchange_time=event_time,
        source_time=event_time,
        receive_time=receive_time,
        processing_time=receive_time,
        decision_time=None,
        sequence=sequence,
        price=price,
        quantity=None,
        volume=100.0 if price is not None else None,
        bid=None if price is None else price - 0.05,
        ask=None if price is None else price + 0.05,
        payload_hash=sha256(payload),
        quality=quality,
        correction=CorrectionStatus.NONE,
        live_trading=False,
    )
