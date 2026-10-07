"""Single-flight Kite history loader. GUI thread consumes GET-only worker results."""

from __future__ import annotations

import time
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor

from quantlab.realtime_data.candles import CandleSeries, ChartRequest, KiteCandleClient
from quantlab.realtime_data.errors import RealTimeDataError


class ChartDataSession:
    def __init__(
        self,
        *,
        fetch: Callable[[ChartRequest], CandleSeries] | None = None,
        timer: Callable[[], float] = time.monotonic,
    ) -> None:
        self._fetch = fetch or KiteCandleClient().fetch
        self._timer = timer
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="kite-chart")
        self._future: Future[CandleSeries] | None = None
        self._submitted: ChartRequest | None = None
        self.request: ChartRequest | None = None
        self.series: CandleSeries | None = None
        self.error: str | None = None
        self.revision = 0
        self._next = 0.0
        self._last_start = -100.0
        self._closed = False
        self._auth_blocked = False
        self._manual = False

    @property
    def busy(self) -> bool:
        return self._future is not None

    def select(self, request: ChartRequest) -> None:
        if request == self.request:
            return
        self.request = request
        self.series = None
        self.error = None
        self._auth_blocked = False
        self._next = 0
        self.revision += 1

    def refresh(self) -> None:
        self._auth_blocked = False
        self._next = 0
        self._manual = True

    def tick(self, *, enabled: bool, auto_refresh: bool = True) -> None:
        if self._closed:
            return
        now = self._timer()
        if self._future is not None and self._future.done():
            pending, self._future = self._future, None
            if self._submitted == self.request:
                try:
                    series = pending.result()
                    if series.request != self.request or series.source != "kite-historical-v3":
                        raise RealTimeDataError("Chart rejected mismatched or non-Kite history")
                    self.series, self.error = series, None
                except Exception as exc:
                    self.error = (
                        str(exc)
                        if isinstance(exc, RealTimeDataError)
                        else ("Kite chart capture failed; check configuration or connectivity")
                    )
                    self._auth_blocked = "authentication rejected" in self.error
                    self._next = now + 60
                self.revision += 1
        if (
            enabled
            and self.request
            and not self._future
            and not self._auth_blocked
            and now >= self._next
            and now - self._last_start >= 2
            and (auto_refresh or self._manual or self.series is None)
        ):
            self._submitted = self.request
            self._last_start = now
            self._next = now + 20
            self._manual = False
            self._future = self._executor.submit(self._fetch, self.request)

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        if self._future:
            self._future.cancel()
        self._executor.shutdown(wait=False, cancel_futures=True)
