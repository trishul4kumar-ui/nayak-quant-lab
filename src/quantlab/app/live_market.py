"""Bounded desktop quote session. No Qt, broker client, or order capabilities.

The GUI owns this object and calls tick(); a single worker performs network I/O.
Only the GUI consumes completed futures. Paused/closed generations discard late
results. REST polling is not a sequence-guaranteed tick stream.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from datetime import UTC, datetime
from time import monotonic
from typing import Any
from zoneinfo import ZoneInfo

from quantlab.realtime_data.errors import RealTimeDataError
from quantlab.realtime_data.models import QualityStatus, RealTimeSnapshot, SessionState
from quantlab.realtime_data.service import fetch_kite_snapshot

IST = ZoneInfo("Asia/Kolkata")


def display_time(value: datetime | None) -> str:
    return value.astimezone(IST).strftime("%d %b %H:%M:%S IST") if value else "—"


@dataclass(frozen=True)
class QuotePoint:
    time: datetime
    price: float
    segment: int


class LiveMarketFeed:
    def __init__(
        self,
        *,
        fetch: Callable[[], RealTimeSnapshot] = fetch_kite_snapshot,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
        timer: Callable[[], float] = monotonic,
        interval_seconds: float = 2.0,
        history_limit: int = 1800,
    ) -> None:
        if interval_seconds < 2 or history_limit < 1:
            raise ValueError("quote polling requires interval >= 2s and bounded positive history")
        self._fetch = fetch
        self._clock = clock
        self._timer = timer
        self.interval_seconds = interval_seconds
        self._history_limit = history_limit
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="kite-quotes")
        self._future: Future[RealTimeSnapshot] | None = None
        self._generation = 0
        self._submitted_generation = 0
        self._next_poll = 0.0
        self._last_request_start = float("-inf")
        self._failures = 0
        self._segment = 0
        self._history: dict[str, deque[QuotePoint]] = {}
        self.enabled = False
        self.closed = False
        self.snapshot: RealTimeSnapshot | None = None
        self.error: str | None = None
        self.revision = 0

    @property
    def busy(self) -> bool:
        return self._future is not None

    def start(self) -> None:
        if self.closed:
            return
        if not self.enabled:
            self._generation += 1
            self.enabled = True
            self._next_poll = max(self._timer(), self._last_request_start + self.interval_seconds)
        self.tick()

    def refresh_now(self) -> None:
        # Manual clicks also respect the request-start cadence and single-flight guard.
        self._next_poll = min(self._next_poll, self._last_request_start + self.interval_seconds)
        self.start()

    def pause(self) -> None:
        self.enabled = False
        self._generation += 1
        self._segment += 1
        self.revision += 1

    def tick(self) -> None:
        if self.closed:
            return
        now = self._timer()
        if self._future is not None and self._future.done():
            future, self._future = self._future, None
            if self.enabled and self._submitted_generation == self._generation:
                try:
                    frozen = future.result()
                    if (
                        frozen.live_trading
                        or frozen.extras.get("active_source") != "kite-rest-quote-v3"
                        or any(
                            row.source != "kite-rest-quote-v3" or row.live_trading
                            for row in frozen.observations
                        )
                    ):
                        raise RealTimeDataError(
                            "Kite display rejected non-Kite or trading-enabled data"
                        )
                except Exception as exc:
                    # Known provider errors are already redacted by the GET-only adapter.
                    # Never display arbitrary exception text (may contain credentials).
                    self.error = (
                        str(exc)
                        if isinstance(exc, RealTimeDataError)
                        else "Kite quote capture failed; check configuration or connectivity"
                    )
                    self._failures += 1
                    self._segment += 1
                    self._next_poll = now + min(60.0, 2.0 ** min(self._failures + 1, 6))
                    if "authentication rejected" in self.error:
                        # Login is required, not repeated unauthenticated calls.
                        self.enabled = False
                else:
                    self.snapshot = frozen
                    self.error = None
                    self._failures = 0
                    self._remember(frozen)
                self.revision += 1
        if self.enabled and self._future is None and now >= self._next_poll:
            self._submitted_generation = self._generation
            self._last_request_start = now
            self._next_poll = now + self.interval_seconds
            self._future = self._executor.submit(self._fetch)

    @property
    def status(self) -> str:
        if self.error:
            return "AUTH REQUIRED" if "authentication rejected" in self.error else "ERROR"
        if not self.enabled:
            return "PAUSED" if self.snapshot else "DISCONNECTED"
        if self.snapshot is None:
            return "CONNECTING"
        if self.snapshot.session is SessionState.CLOSED:
            return "MARKET CLOSED"
        rows = self.quote_rows()
        if any(row["quality"] == "stale" for row in rows):
            return "STALE"
        if not rows or any(row["quality"] != "valid" for row in rows):
            return "DEGRADED"
        return (
            "LIVE QUOTES"
            if self.snapshot.session is SessionState.OPEN
            else self.snapshot.session.value.upper().replace("_", " ")
        )

    def quote_rows(self) -> list[dict[str, Any]]:
        frozen = self.snapshot
        if frozen is None:
            return []
        observed = {row.security_id: row for row in frozen.observations}
        configured = frozen.extras.get("configured_instruments", tuple(observed))
        symbols = list(configured) if isinstance(configured, tuple | list) else list(observed)
        max_age = float(frozen.extras.get("max_quote_age_seconds", 5.0))
        now = self._clock()
        rows: list[dict[str, Any]] = []
        for symbol in symbols:
            item = observed.get(str(symbol))
            timestamp = item.exchange_time if item else None
            age = (now - timestamp).total_seconds() if timestamp else None
            quality = item.quality.value if item else "missing"
            if age is not None and age > max_age:
                quality = "stale"
            if age is not None and age < -1:
                quality = "degraded"
            if self.error:
                quality = "unavailable"
            elif not self.enabled:
                quality = "paused" if item else "missing"
            rows.append(
                {
                    "instrument": str(symbol),
                    "price": item.price if item else None,
                    "bid": item.bid if item else None,
                    "ask": item.ask if item else None,
                    "volume": item.volume if item else None,
                    "quote_time": timestamp,
                    "receive_time": item.receive_time if item else None,
                    "age_seconds": age,
                    "quality": quality,
                    "source": item.source if item else "kite-rest-quote-v3",
                    "note": item.note
                    if item
                    else "Configured instrument absent from provider response",
                }
            )
        return rows

    def history(self, instrument: str) -> list[QuotePoint]:
        return list(self._history.get(instrument, ()))

    def _remember(self, frozen: RealTimeSnapshot) -> None:
        max_age = float(frozen.extras.get("max_quote_age_seconds", 5.0))
        for row in frozen.observations:
            timestamp = row.exchange_time
            if (
                timestamp is None
                or row.price is None
                or row.quality is not QualityStatus.VALID
                or not 0 <= (self._clock() - timestamp).total_seconds() <= max_age
            ):
                continue
            history = self._history.setdefault(row.security_id, deque(maxlen=self._history_limit))
            if history and timestamp <= history[-1].time:
                continue
            if (
                history
                and timestamp.astimezone(IST).date() != history[-1].time.astimezone(IST).date()
            ):
                history.clear()
            history.append(QuotePoint(timestamp, row.price, self._segment))

    def close(self) -> None:
        if self.closed:
            return
        self.pause()
        self.closed = True
        self._executor.shutdown(wait=False, cancel_futures=True)
