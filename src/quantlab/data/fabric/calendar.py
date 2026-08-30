"""Trading calendar. Does not invent official NSE holidays."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from typing import Protocol

from quantlab.core.time import IST, as_utc


class TradingCalendar(Protocol):
    exchange: str
    segment: str
    version: str
    provenance: str

    def is_session(self, day: date) -> bool: ...

    def sessions(self, start: date, end: date) -> list[date]: ...

    def session_open(self, day: date) -> datetime: ...

    def session_close(self, day: date) -> datetime: ...


class WeekdayCalendar:
    """Mon–Fri cash sessions in Asia/Kolkata.

    This is NOT an official NSE holiday calendar. Holidays must be supplied
    by a sourced file or derived from observed bar sessions.
    """

    def __init__(
        self,
        *,
        exchange: str = "NSE",
        segment: str = "CM",
        holidays: frozenset[date] | None = None,
        provenance: str = "synthetic_weekdays_not_official_nse_holidays",
        version: str = "weekday-v1",
    ) -> None:
        self.exchange = exchange
        self.segment = segment
        self.holidays = holidays or frozenset()
        self.provenance = provenance
        self.version = version

    def is_session(self, day: date) -> bool:
        return day.weekday() < 5 and day not in self.holidays

    def sessions(self, start: date, end: date) -> list[date]:
        if end < start:
            return []
        out: list[date] = []
        cursor = start
        while cursor <= end:
            if self.is_session(cursor):
                out.append(cursor)
            cursor += timedelta(days=1)
        return out

    def session_open(self, day: date) -> datetime:
        return as_utc(datetime.combine(day, time(9, 15), tzinfo=IST))

    def session_close(self, day: date) -> datetime:
        return as_utc(datetime.combine(day, time(15, 30), tzinfo=IST))


def calendar_from_sessions(
    session_days: list[date],
    *,
    exchange: str = "NSE",
    segment: str = "CM",
) -> WeekdayCalendar:
    """Derive a calendar from observed bars. Provenance is explicit."""
    observed = frozenset(session_days)
    if not session_days:
        return WeekdayCalendar(exchange=exchange, segment=segment, holidays=frozenset())
    start = min(session_days)
    end = max(session_days)
    holidays: set[date] = set()
    cursor = start
    while cursor <= end:
        if cursor.weekday() < 5 and cursor not in observed:
            holidays.add(cursor)
        cursor += timedelta(days=1)
    return WeekdayCalendar(
        exchange=exchange,
        segment=segment,
        holidays=frozenset(holidays),
        provenance="derived_from_observed_bar_sessions",
        version="observed-v1",
    )


def session_date_ist(value: datetime) -> date:
    return value.astimezone(IST).date()


class SourcedCalendar(WeekdayCalendar):
    """Calendar whose holidays come from an explicit source. Not invented NSE holidays."""

    def __init__(
        self,
        *,
        exchange: str,
        holidays: frozenset[date],
        source: str,
        version: str,
        timezone: str = "Asia/Kolkata",
        special_sessions: frozenset[date] | None = None,
        half_days: frozenset[date] | None = None,
    ) -> None:
        if not source.strip():
            raise ValueError("sourced calendar requires an explicit source")
        super().__init__(
            exchange=exchange,
            holidays=holidays,
            provenance=source,
            version=version,
        )
        self.timezone = timezone
        self.special_sessions = special_sessions or frozenset()
        self.half_days = half_days or frozenset()
        self.source = source
