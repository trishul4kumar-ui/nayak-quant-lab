"""Kite Connect v3 quote polling adapter.

The adapter has a deliberately narrow surface: it can only issue GET requests to
the documented ``/quote`` endpoint.  It is an observe-only source for frozen
market snapshots; it is not a Kite order client and it never imports one.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from quantlab.realtime_data.errors import RealTimeDataError
from quantlab.realtime_data.hashing import sha256
from quantlab.realtime_data.models import MarketObservation, QualityStatus
from quantlab.realtime_data.production import ProductionFeedSource, ProductionMarketDataAdapter

_BASE_URL = "https://api.kite.trade"
_SOURCE_ID = "kite-rest-quote-v3"
_IST = ZoneInfo("Asia/Kolkata")
_MAX_QUOTE_INSTRUMENTS = 500


@dataclass(frozen=True)
class KiteHttpResponse:
    status: int
    body: bytes


class KiteQuoteTransport(Protocol):
    """GET-only transport: its protocol intentionally has no write method."""

    def get(
        self, path: str, headers: Mapping[str, str], timeout_seconds: float
    ) -> KiteHttpResponse: ...


class UrllibKiteQuoteTransport:
    """HTTPS transport restricted to Kite's API base URL and GET requests."""

    def get(
        self, path: str, headers: Mapping[str, str], timeout_seconds: float
    ) -> KiteHttpResponse:
        request = Request(f"{_BASE_URL}{path}", headers=dict(headers), method="GET")
        try:
            with urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310 - fixed HTTPS host
                return KiteHttpResponse(status=int(response.status), body=response.read())
        except HTTPError as exc:
            return KiteHttpResponse(status=int(exc.code), body=exc.read())
        except URLError as exc:
            raise RealTimeDataError(
                f"Kite quote network failure: {type(exc.reason).__name__}"
            ) from None


class KiteMarketDataConfig(BaseSettings):
    """Environment-only configuration. Credentials are never persisted or logged."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", populate_by_name=True)

    api_key: str = Field(default="", validation_alias=AliasChoices("KITE_API_KEY", "api_key"))
    access_token: str = Field(
        default="", validation_alias=AliasChoices("KITE_ACCESS_TOKEN", "access_token")
    )
    symbols: str = Field(default="", validation_alias="KITE_MARKET_DATA_SYMBOLS")
    timeout_seconds: float = Field(default=10.0, validation_alias="KITE_TIMEOUT_SECONDS", gt=0)
    max_quote_age_seconds: float = Field(
        default=5.0,
        validation_alias="KITE_MAX_QUOTE_AGE_SECONDS",
        gt=0,
    )


class KiteMarketDataAdapter(ProductionMarketDataAdapter):
    """Read-only Kite quote source with explicit identity, quality, and provenance."""

    write_enabled = False

    def __init__(
        self,
        config: KiteMarketDataConfig,
        *,
        transport: KiteQuoteTransport | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        if not config.api_key or not config.access_token:
            raise RealTimeDataError("Kite market-data credentials are not configured")
        self._symbols = _configured_symbols(config.symbols)
        super().__init__(
            (ProductionFeedSource(source_id=_SOURCE_ID, priority=1),),
            expected_security_ids=frozenset(self._symbols),
        )
        self._config = config
        self._transport = transport or UrllibKiteQuoteTransport()
        self._clock = clock or (lambda: datetime.now(tz=UTC))
        self._provider_faults: list[str] = []

    @classmethod
    def from_environment(cls) -> KiteMarketDataAdapter:
        return cls(KiteMarketDataConfig())

    @classmethod
    def environment_configured(cls) -> bool:
        try:
            cls.from_environment()
        except RealTimeDataError:
            return False
        return True

    def poll(self) -> tuple[MarketObservation, ...]:
        if not bool(self.source_health()["connected"]):
            return ()
        response = self._transport.get(
            "/quote?" + urlencode([("i", symbol) for symbol in self._symbols.values()]),
            self._headers(),
            self._config.timeout_seconds,
        )
        if response.status in {401, 403}:
            raise RealTimeDataError("Kite quote authentication rejected")
        if response.status != 200:
            raise RealTimeDataError(f"Kite quote request failed ({response.status})")
        payload = _quote_payload(response.body)
        data = payload.get("data")
        if not isinstance(data, dict):
            raise RealTimeDataError("Kite quote response was missing data")

        missing = set(self._symbols.values()) - set(data)
        if missing:
            self._provider_faults.append("missing_configured_instrument")
        received_at = self._clock()
        rows: list[MarketObservation] = []
        for security_id, instrument in self._symbols.items():
            raw = data.get(instrument)
            if not isinstance(raw, dict):
                continue
            rows.append(
                self._observation(
                    security_id,
                    instrument,
                    raw,
                    received_at=received_at,
                    incomplete_response=bool(missing),
                )
            )
        if not rows:
            raise RealTimeDataError("Kite quote response contained no configured instruments")
        self.ingest(_SOURCE_ID, tuple(rows))
        return super().poll()

    def source_health(self) -> dict[str, object]:
        payload = super().source_health()
        payload["configured_instruments"] = tuple(self._symbols.values())
        # `/quote` is a REST snapshot endpoint, not a sequence-bearing stream.
        # Record that limitation explicitly so consumers never infer a sequence.
        payload["sequence_guarantee"] = "not_provided"
        payload["provider_faults"] = tuple(self._provider_faults)
        raw_faults = payload.get("quality_faults")
        faults: tuple[str, ...] = (
            tuple(str(item) for item in raw_faults) if isinstance(raw_faults, tuple) else ()
        )
        payload["quality_faults"] = tuple(dict.fromkeys((*faults, *self._provider_faults)))
        return payload

    def _headers(self) -> dict[str, str]:
        return {
            "X-Kite-Version": "3",
            "Authorization": f"token {self._config.api_key}:{self._config.access_token}",
            "Accept": "application/json",
        }

    def _observation(
        self,
        security_id: str,
        instrument: str,
        raw: dict[str, Any],
        *,
        received_at: datetime,
        incomplete_response: bool,
    ) -> MarketObservation:
        quote_time = _parse_timestamp(raw.get("timestamp"))
        use_receipt_time = quote_time is None
        event_time = quote_time or received_at
        quote_age_seconds = (
            (received_at - quote_time).total_seconds() if quote_time is not None else None
        )
        stale_quote = (
            quote_age_seconds is not None and quote_age_seconds > self._config.max_quote_age_seconds
        )
        exchange, _, _symbol = instrument.partition(":")
        price = _number(raw.get("last_price"))
        bid, ask = _best_quote(raw.get("depth"))
        degraded = incomplete_response or use_receipt_time
        payload = {
            "instrument": instrument,
            "instrument_token": raw.get("instrument_token"),
            "last_price": price,
            "last_quantity": _number(raw.get("last_quantity")),
            "volume": _number(raw.get("volume")),
            "bid": bid,
            "ask": ask,
            "timestamp": raw.get("timestamp"),
            "source": _SOURCE_ID,
        }
        note_parts = ["Kite REST /quote observation. Not a signal and not an order."]
        if use_receipt_time:
            note_parts.append(
                "Provider quote timestamp missing; receipt time used and quality degraded."
            )
        elif stale_quote:
            note_parts.append(
                "Provider quote timestamp exceeds the configured maximum quote age; quality stale."
            )
        if incomplete_response:
            note_parts.append("One or more configured instruments were absent; quality degraded.")
        return MarketObservation(
            observation_id=f"kite-{sha256(payload)[:16]}",
            security_id=security_id,
            venue=exchange,
            source=_SOURCE_ID,
            event_time=event_time,
            exchange_time=quote_time,
            source_time=quote_time,
            receive_time=received_at,
            processing_time=self._clock(),
            sequence=None,
            price=price,
            quantity=_number(raw.get("last_quantity")),
            volume=_number(raw.get("volume")),
            bid=bid,
            ask=ask,
            provenance="kite-rest-quote-v3",
            payload_hash=sha256(payload),
            quality=(
                QualityStatus.STALE
                if stale_quote
                else QualityStatus.DEGRADED
                if degraded
                else QualityStatus.VALID
            ),
            live_trading=False,
            note=" ".join(note_parts),
        )


def _configured_symbols(raw: str) -> dict[str, str]:
    symbols = [value.strip().upper() for value in raw.split(",") if value.strip()]
    if not symbols:
        raise RealTimeDataError("KITE_MARKET_DATA_SYMBOLS must list EXCHANGE:SYMBOL values")
    if len(symbols) > _MAX_QUOTE_INSTRUMENTS:
        raise RealTimeDataError(
            f"Kite /quote supports at most {_MAX_QUOTE_INSTRUMENTS} instruments"
        )
    if len(symbols) != len(set(symbols)):
        raise RealTimeDataError("KITE_MARKET_DATA_SYMBOLS contains duplicate instruments")
    for symbol in symbols:
        exchange, separator, tradingsymbol = symbol.partition(":")
        if not separator or not exchange or not tradingsymbol:
            raise RealTimeDataError("KITE_MARKET_DATA_SYMBOLS must use EXCHANGE:SYMBOL values")
    return {symbol: symbol for symbol in symbols}


def _quote_payload(body: bytes) -> dict[str, Any]:
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise RealTimeDataError("Kite quote response was not valid JSON") from None
    if not isinstance(payload, dict) or payload.get("status") != "success":
        raise RealTimeDataError("Kite quote response was unsuccessful")
    return payload


def _parse_timestamp(value: object) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip()
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=_IST)
    return parsed.astimezone(UTC)


def _number(value: object) -> float | None:
    if isinstance(value, int | float) and not isinstance(value, bool):
        return float(value)
    return None


def _best_quote(depth: object) -> tuple[float | None, float | None]:
    if not isinstance(depth, dict):
        return None, None
    buy = depth.get("buy")
    sell = depth.get("sell")
    first_buy = buy[0] if isinstance(buy, list) and buy else None
    first_sell = sell[0] if isinstance(sell, list) and sell else None
    bid = _positive_number(first_buy.get("price")) if isinstance(first_buy, dict) else None
    ask = _positive_number(first_sell.get("price")) if isinstance(first_sell, dict) else None
    return bid, ask


def _positive_number(value: object) -> float | None:
    number = _number(value)
    return number if number is not None and number > 0 else None
