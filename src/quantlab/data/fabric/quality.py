"""Quality engine. Invalid bars never reach curated/PIT storage."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from quantlab.core.errors import DataIntegrityError
from quantlab.data.fabric.calendar import TradingCalendar, session_date_ist
from quantlab.data.validation import validate_bar
from quantlab.domain.models import OHLCVBar


class QuarantineRecord(BaseModel):
    reason: str
    instrument: str
    event_time: datetime | None = None
    detail: str = ""


class DataQualityReport(BaseModel):
    rows_ingested: int = 0
    rows_accepted: int = 0
    rows_rejected: int = 0
    duplicate_count: int = 0
    missing_sessions: int = 0
    invalid_count: int = 0
    instrument_count: int = 0
    quarantine: list[QuarantineRecord] = Field(default_factory=list)

    def ok_for_curated(self) -> bool:
        return self.rows_accepted > 0 and self.invalid_count == 0


def assess_bars(
    bars: list[OHLCVBar],
    calendar: TradingCalendar | None = None,
) -> tuple[list[OHLCVBar], DataQualityReport]:
    report = DataQualityReport(rows_ingested=len(bars))
    accepted: list[OHLCVBar] = []
    seen: set[tuple[str, datetime]] = set()
    instruments: set[str] = set()
    for bar in bars:
        instruments.add(str(bar.instrument))
        key = (str(bar.instrument), bar.pit.event_time)
        if key in seen:
            report.duplicate_count += 1
            report.rows_rejected += 1
            report.quarantine.append(
                QuarantineRecord(
                    reason="duplicate",
                    instrument=str(bar.instrument),
                    event_time=bar.pit.event_time,
                )
            )
            continue
        seen.add(key)
        try:
            validate_bar(bar)
        except DataIntegrityError as exc:
            report.invalid_count += 1
            report.rows_rejected += 1
            report.quarantine.append(
                QuarantineRecord(
                    reason="invalid_ohlc_or_pit",
                    instrument=str(bar.instrument),
                    event_time=bar.pit.event_time,
                    detail=str(exc),
                )
            )
            continue
        if bar.pit.event_time.tzinfo is None:
            report.invalid_count += 1
            report.rows_rejected += 1
            report.quarantine.append(
                QuarantineRecord(
                    reason="naive_timestamp",
                    instrument=str(bar.instrument),
                    event_time=None,
                )
            )
            continue
        accepted.append(bar)
        report.rows_accepted += 1
    report.instrument_count = len(instruments)
    if calendar is not None and accepted:
        by_inst: dict[str, list[OHLCVBar]] = {}
        for bar in accepted:
            by_inst.setdefault(str(bar.instrument), []).append(bar)
        for series in by_inst.values():
            series.sort(key=lambda b: b.pit.event_time)
            start = session_date_ist(series[0].pit.event_time)
            end = session_date_ist(series[-1].pit.event_time)
            expected = set(calendar.sessions(start, end))
            got = {session_date_ist(b.pit.event_time) for b in series}
            report.missing_sessions += len(expected - got)
    return accepted, report
