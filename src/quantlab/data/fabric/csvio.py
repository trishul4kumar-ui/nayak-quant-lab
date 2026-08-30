"""CSV and synthetic bar serialization. Naive timestamps are rejected."""

from __future__ import annotations

import csv
import io
from datetime import date, datetime
from pathlib import Path

from quantlab.core.errors import DataIntegrityError
from quantlab.core.identifiers import InstrumentId
from quantlab.core.time import PointInTime, as_utc
from quantlab.data.fabric.calendar import WeekdayCalendar, session_date_ist
from quantlab.data.fabric.types import DataKind, PriceKind
from quantlab.domain.models import BarInterval, OHLCVBar

CSV_FIELDS = (
    "exchange",
    "symbol",
    "event_time",
    "effective_time",
    "available_time",
    "open",
    "high",
    "low",
    "close",
    "volume",
)


def bars_to_csv_bytes(bars: list[OHLCVBar]) -> bytes:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=CSV_FIELDS, lineterminator="\n")
    writer.writeheader()
    for bar in bars:
        writer.writerow(
            {
                "exchange": bar.instrument.exchange,
                "symbol": bar.instrument.symbol,
                "event_time": as_utc(bar.pit.event_time).isoformat(),
                "effective_time": as_utc(bar.pit.effective_time).isoformat(),
                "available_time": as_utc(bar.pit.available_time).isoformat(),
                "open": f"{bar.open:.10f}",
                "high": f"{bar.high:.10f}",
                "low": f"{bar.low:.10f}",
                "close": f"{bar.close:.10f}",
                "volume": f"{bar.volume:.10f}",
            }
        )
    return buffer.getvalue().encode("utf-8")


def parse_timestamp(raw: str, calendar: WeekdayCalendar) -> tuple[datetime, str]:
    text = raw.strip()
    if not text:
        raise DataIntegrityError("empty timestamp")
    if len(text) == 10 and text[4] == "-" and text[7] == "-":
        day = date.fromisoformat(text)
        return calendar.session_close(day), "session_close"
    parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise DataIntegrityError(
            "naive datetime rejected; use an offset or a date-only session close"
        )
    return as_utc(parsed), "explicit"


def parse_ohlcv_csv(
    path: Path,
    *,
    data_kind: DataKind,
    dataset_version: str,
    source_id: str,
    calendar: WeekdayCalendar | None = None,
) -> tuple[list[OHLCVBar], str]:
    calendar = calendar or WeekdayCalendar()
    conventions: set[str] = set()
    bars: list[OHLCVBar] = []
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise DataIntegrityError("CSV has no header")
        fields = {name.strip().lower(): name for name in reader.fieldnames}
        for row in reader:
            if not any(v.strip() for v in row.values() if v is not None):
                continue
            symbol = _cell(row, fields, "symbol")
            exchange = _optional(row, fields, "exchange") or "NSE"
            event_raw = _first(row, fields, ("event_time", "timestamp", "date"))
            event, convention = parse_timestamp(event_raw, calendar)
            conventions.add(convention)
            available_raw = _optional(row, fields, "available_time")
            if available_raw:
                available, avail_conv = parse_timestamp(available_raw, calendar)
                conventions.add(avail_conv)
            else:
                available = event if convention == "explicit" else event
                conventions.add(convention)
            effective_raw = _optional(row, fields, "effective_time")
            if effective_raw:
                effective, _ = parse_timestamp(effective_raw, calendar)
            else:
                effective = event
            bar = OHLCVBar(
                instrument=InstrumentId(exchange=exchange, symbol=symbol.upper()),
                pit=PointInTime(
                    event_time=event,
                    effective_time=effective,
                    available_time=available,
                    ingestion_time=event,
                ),
                interval=BarInterval.DAY,
                open=float(_cell(row, fields, "open")),
                high=float(_cell(row, fields, "high")),
                low=float(_cell(row, fields, "low")),
                close=float(_cell(row, fields, "close")),
                volume=float(_optional(row, fields, "volume") or "0"),
                dataset_version=dataset_version,
                source_id=source_id,
                session_date=session_date_ist(event).isoformat(),
                price_kind=PriceKind.RAW_PRICE.value,
                data_kind=data_kind.value,
            )
            bars.append(bar)
    if not bars:
        raise DataIntegrityError("CSV contained no OHLCV rows")
    convention = "session_close" if "session_close" in conventions else "explicit"
    return bars, convention


def _cell(row: dict[str, str | None], fields: dict[str, str], name: str) -> str:
    key = fields.get(name)
    if key is None:
        raise DataIntegrityError(f"CSV missing column {name}")
    value = row.get(key)
    if value is None or not str(value).strip():
        raise DataIntegrityError(f"CSV missing value for {name}")
    return str(value).strip()


def _optional(row: dict[str, str | None], fields: dict[str, str], name: str) -> str | None:
    key = fields.get(name)
    if key is None:
        return None
    value = row.get(key)
    if value is None or not str(value).strip():
        return None
    return str(value).strip()


def _first(row: dict[str, str | None], fields: dict[str, str], names: tuple[str, ...]) -> str:
    for name in names:
        value = _optional(row, fields, name)
        if value:
            return value
    raise DataIntegrityError(f"CSV missing one of {', '.join(names)}")
