"""Bounded GET-only Kite historical candles, never reconstructed from quote polls."""

from __future__ import annotations

import json
import math
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

from quantlab.realtime_data.errors import RealTimeDataError
from quantlab.realtime_data.kite import (
    KiteMarketDataConfig,
    KiteQuoteTransport,
    UrllibKiteQuoteTransport,
    _configured_symbols,
)
from quantlab.realtime_data.service import _assert_safety

IST = ZoneInfo("Asia/Kolkata")
INTERVALS = {
    "minute": 60,
    "3minute": 180,
    "5minute": 300,
    "10minute": 600,
    "15minute": 900,
    "30minute": 1800,
    "60minute": 3600,
    "day": 86400,
}


@dataclass(frozen=True)
class ChartRequest:
    instrument: str
    interval: str = "minute"
    days: int = 5


@dataclass(frozen=True)
class Candle:
    time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float | None


@dataclass(frozen=True)
class CandleSeries:
    request: ChartRequest
    candles: tuple[Candle, ...]
    fetched_at: datetime
    source: str = "kite-historical-v3"

    def is_forming(self, candle: Candle) -> bool:
        return candle.time + timedelta(seconds=INTERVALS[self.request.interval]) > self.fetched_at


class KiteCandleClient:
    """One worker owns this client. Tokens are cached for a day, never guessed."""

    def __init__(
        self,
        *,
        transport: KiteQuoteTransport | None = None,
        clock: Callable[[], datetime] | None = None,
        config: Callable[[], KiteMarketDataConfig] = KiteMarketDataConfig,
    ) -> None:
        self._transport = transport or UrllibKiteQuoteTransport()
        self._clock = clock or (lambda: datetime.now(UTC))
        self._config = config
        self._tokens: dict[str, int] = {}
        self._token_day = ""

    def fetch(self, request: ChartRequest) -> CandleSeries:
        _assert_safety()
        if request.interval not in INTERVALS:
            raise RealTimeDataError("Unsupported Kite candle interval")
        maximum = 366 if request.interval == "day" else 31
        if not 1 <= request.days <= maximum:
            raise RealTimeDataError(f"Chart history range must be between 1 and {maximum} days")
        cfg = self._config()
        if not cfg.api_key or not cfg.access_token:
            raise RealTimeDataError("Kite market-data credentials are not configured")
        if request.instrument not in _configured_symbols(cfg.symbols):
            raise RealTimeDataError("Chart instrument must belong to the configured Kite watchlist")
        now = self._clock()
        today = now.astimezone(IST).date().isoformat()
        if self._token_day != today:
            self._tokens.clear()
            self._token_day = today
        headers = {
            "X-Kite-Version": "3",
            "Authorization": f"token {cfg.api_key}:{cfg.access_token}",
        }
        token = self._tokens.get(request.instrument)
        if token is None:
            payload = self._get("/quote?" + urlencode({"i": request.instrument}), headers, cfg)
            data = payload.get("data")
            quote = data.get(request.instrument) if isinstance(data, dict) else None
            raw_token = quote.get("instrument_token") if isinstance(quote, dict) else None
            if not isinstance(raw_token, int) or isinstance(raw_token, bool) or raw_token <= 0:
                raise RealTimeDataError("Kite did not provide a chart instrument token")
            token = raw_token
            if len(self._tokens) >= 500:
                self._tokens.clear()
            self._tokens[request.instrument] = token
        start = (now.astimezone(IST) - timedelta(days=request.days - 1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        query = urlencode(
            {
                "from": start.strftime("%Y-%m-%d %H:%M:%S"),
                "to": now.astimezone(IST).strftime("%Y-%m-%d %H:%M:%S"),
                "continuous": 0,
                "oi": 0,
            }
        )
        payload = self._get(
            f"/instruments/historical/{token}/{request.interval}?{query}", headers, cfg
        )
        data = payload.get("data")
        raw = data.get("candles") if isinstance(data, dict) else None
        if not isinstance(raw, list) or len(raw) > 12000:
            raise RealTimeDataError("Kite candle response missing or exceeds the chart bound")
        candles = tuple(_candle(row) for row in raw)
        if any(row.time < start or row.time > now for row in candles):
            raise RealTimeDataError("Kite candle timestamps were outside the requested period")
        if any(b.time <= a.time for a, b in zip(candles, candles[1:], strict=False)):
            raise RealTimeDataError("Kite candles were duplicated or not chronological")
        _assert_safety()
        return CandleSeries(request, candles, self._clock())

    def _get(
        self, path: str, headers: dict[str, str], cfg: KiteMarketDataConfig
    ) -> dict[str, object]:
        response = self._transport.get(path, headers, cfg.timeout_seconds)
        if response.status in {401, 403}:
            raise RealTimeDataError("Kite chart authentication rejected; renew Kite login")
        if response.status != 200:
            raise RealTimeDataError(f"Kite chart data unavailable (HTTP {response.status})")
        try:
            payload = json.loads(response.body)
        except (ValueError, UnicodeDecodeError):
            raise RealTimeDataError("Kite chart response was not valid JSON") from None
        if not isinstance(payload, dict) or payload.get("status") != "success":
            raise RealTimeDataError("Kite chart response was unsuccessful")
        return payload


def _candle(raw: object) -> Candle:
    try:
        if not isinstance(raw, list) or len(raw) not in {6, 7} or not isinstance(raw[0], str):
            raise ValueError
        time = datetime.fromisoformat(raw[0])
        if time.tzinfo is None:
            raise ValueError
        values: list[float] = []
        for value in raw[1:5]:
            if isinstance(value, bool) or not isinstance(value, int | float):
                raise ValueError
            values.append(float(value))
        opening, high, low, close = values
        v = raw[5]
        if v is not None and (isinstance(v, bool) or not isinstance(v, int | float)):
            raise ValueError
        volume = float(v) if v is not None else None
        if not all(math.isfinite(value) and value > 0 for value in values):
            raise ValueError
        if not low <= min(opening, close) <= max(opening, close) <= high:
            raise ValueError
        if volume is not None and (not math.isfinite(volume) or volume < 0):
            raise ValueError
        return Candle(time.astimezone(UTC), opening, high, low, close, volume)
    except (TypeError, ValueError, OverflowError):
        raise RealTimeDataError("Kite candle contains invalid timestamp, OHLC or volume") from None
