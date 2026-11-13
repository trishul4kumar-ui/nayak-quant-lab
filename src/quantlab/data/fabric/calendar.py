"""Trading calendar. Does not invent official NSE holidays."""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Protocol
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import TypeAdapter

from quantlab.control_plane.sqlite import ControlPlaneSqlite, ControlPlaneStoreError
from quantlab.core.errors import DataIntegrityError
from quantlab.core.time import IST, as_utc
from quantlab.data.fabric.types import DataKind
from quantlab.data.policy import require_real_data


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
        special_hours: tuple[SessionOverride, ...] = (),
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
        self.special_hours = {row.day: row for row in special_hours}
        if len(self.special_hours) != len(special_hours):
            raise ValueError("duplicate special session dates")
        if self.special_sessions & self.holidays:
            raise ValueError("a date cannot be both a holiday and a special session")
        try:
            ZoneInfo(timezone)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise ValueError("unknown calendar timezone") from exc
        self.source = source

    def is_session(self, day: date) -> bool:
        return day in self.special_sessions or super().is_session(day)

    def _hours(self, day: date) -> tuple[time, time]:
        if not self.is_session(day):
            raise DataIntegrityError("calendar date is not a trading session")
        override = self.special_hours.get(day)
        if override is not None:
            return override.opens, override.closes
        if day in self.special_sessions or day in self.half_days:
            raise DataIntegrityError("special session hours are unavailable")
        return time(9, 15), time(15, 30)

    def session_open(self, day: date) -> datetime:
        return _unambiguous_session_time(day, self._hours(day)[0], ZoneInfo(self.timezone))

    def session_close(self, day: date) -> datetime:
        return _unambiguous_session_time(day, self._hours(day)[1], ZoneInfo(self.timezone))


@dataclass(frozen=True)
class SessionOverride:
    """Explicit hours for a special or shortened session in the exchange timezone."""

    day: date
    opens: time
    closes: time

    def __post_init__(self) -> None:
        if self.opens.tzinfo is not None or self.closes.tzinfo is not None:
            raise ValueError("session hours must be local times without a timezone")
        if self.opens >= self.closes:
            raise ValueError("session open must precede session close")


@dataclass(frozen=True)
class CalendarSnapshot:
    """One sourced calendar revision; timestamps describe when it became known.

    The supplied checksum identifies source bytes; it does not certify their
    authenticity or prove the extracted calendar faithfully represents them.
    """

    exchange: str
    segment: str
    version: str
    source: str
    source_sha256: str
    published_at: datetime
    available_at: datetime
    coverage_start: date
    coverage_end: date
    timezone: str
    regular_open: time
    regular_close: time
    holidays: frozenset[date]
    special_sessions: tuple[SessionOverride, ...] = ()
    data_kind: DataKind = DataKind.SYNTHETIC

    def __post_init__(self) -> None:
        if not all(
            value.strip() for value in (self.exchange, self.segment, self.version, self.source)
        ):
            raise ValueError("calendar identity and source must be non-empty")
        if len(self.source_sha256) != 64 or any(
            char not in "0123456789abcdef" for char in self.source_sha256
        ):
            raise ValueError("calendar source checksum must be a lowercase SHA-256")
        if self.published_at.utcoffset() is None or self.available_at.utcoffset() is None:
            raise ValueError("calendar source times must be timezone-aware")
        if self.available_at < self.published_at:
            raise ValueError("calendar availability cannot precede publication")
        if self.coverage_start > self.coverage_end:
            raise ValueError("calendar coverage is reversed")
        try:
            ZoneInfo(self.timezone)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise ValueError("unknown calendar timezone") from exc
        if self.regular_open.tzinfo is not None or self.regular_close.tzinfo is not None:
            raise ValueError("regular hours must be local times without a timezone")
        if self.regular_open >= self.regular_close:
            raise ValueError("regular session open must precede close")
        special_days = [item.day for item in self.special_sessions]
        if len(special_days) != len(set(special_days)):
            raise ValueError("duplicate special session dates")
        if any(not self.coverage_start <= day <= self.coverage_end for day in self.holidays):
            raise ValueError("holiday outside calendar coverage")
        if any(not self.coverage_start <= day <= self.coverage_end for day in special_days):
            raise ValueError("special session outside calendar coverage")
        if set(special_days) & self.holidays:
            raise ValueError("a date cannot be both a holiday and a special session")
        if not isinstance(self.holidays, frozenset) or not isinstance(self.special_sessions, tuple):
            raise ValueError("calendar dates must use immutable collections")

    def source_matches(self, raw_bytes: bytes) -> bool:
        return hashlib.sha256(raw_bytes).hexdigest() == self.source_sha256

    def session(self, day: date) -> tuple[datetime, datetime] | None:
        if not self.coverage_start <= day <= self.coverage_end:
            raise DataIntegrityError("calendar date outside recorded coverage")
        override = next((item for item in self.special_sessions if item.day == day), None)
        if override is None and (day.weekday() >= 5 or day in self.holidays):
            return None
        opening = override.opens if override is not None else self.regular_open
        closing = override.closes if override is not None else self.regular_close
        timezone = ZoneInfo(self.timezone)
        return (
            _unambiguous_session_time(day, opening, timezone),
            _unambiguous_session_time(day, closing, timezone),
        )


def _unambiguous_session_time(day: date, value: time, timezone: ZoneInfo) -> datetime:
    local = datetime.combine(day, value, tzinfo=timezone)
    if local.utcoffset() != local.replace(fold=1).utcoffset():
        raise DataIntegrityError("calendar session time is ambiguous or nonexistent")
    result = as_utc(local)
    if result.astimezone(timezone).replace(tzinfo=None) != local.replace(tzinfo=None):
        raise DataIntegrityError("calendar session time is nonexistent")
    return result


class BoundCalendar:
    """TradingCalendar view of one source revision known at one decision cutoff.

    Historical simulations must bind separately for each decision cutoff, not
    reuse a later revision across earlier decisions.
    """

    def __init__(self, snapshot: CalendarSnapshot, *, as_of: datetime) -> None:
        if as_of.utcoffset() is None or snapshot.available_at > as_of:
            raise DataIntegrityError("calendar revision is unavailable at decision cutoff")
        self._snapshot = snapshot
        self.as_of = as_of
        self.exchange = snapshot.exchange
        self.segment = snapshot.segment
        self.version = snapshot.version
        self.provenance = snapshot.source
        self.source_sha256 = snapshot.source_sha256

    def is_session(self, day: date) -> bool:
        return self._snapshot.session(day) is not None

    def sessions(self, start: date, end: date) -> list[date]:
        if end < start:
            return []
        days: list[date] = []
        cursor = start
        while cursor <= end:
            if self.is_session(cursor):
                days.append(cursor)
            cursor += timedelta(days=1)
        return days

    def session_open(self, day: date) -> datetime:
        session = self._snapshot.session(day)
        if session is None:
            raise DataIntegrityError("calendar date is not a trading session")
        return session[0]

    def session_close(self, day: date) -> datetime:
        session = self._snapshot.session(day)
        if session is None:
            raise DataIntegrityError("calendar date is not a trading session")
        return session[1]


class PointInTimeCalendar:
    """Select source revisions known at a decision time, optionally persisted."""

    _namespace = "pit_calendar_snapshots"

    def __init__(
        self, *, exchange: str, segment: str, storage_path: Path | None = None
    ) -> None:
        if not exchange.strip() or not segment.strip():
            raise ValueError("calendar exchange and segment are required")
        self.exchange = exchange
        self.segment = segment
        self._snapshots: list[CalendarSnapshot] = []
        self._source_bytes: dict[str, bytes] = {}
        self._store = ControlPlaneSqlite(storage_path) if storage_path is not None else None

    def close(self) -> None:
        if self._store is not None:
            self._store.close()

    def add(self, snapshot: CalendarSnapshot, *, source_bytes: bytes) -> None:
        if not isinstance(snapshot.data_kind, DataKind):
            raise DataIntegrityError("calendar requires an explicit data-kind label")
        require_real_data(snapshot.data_kind.value, source=snapshot.source)
        if (snapshot.exchange, snapshot.segment) != (self.exchange, self.segment):
            raise DataIntegrityError("calendar exchange or segment mismatch")
        if not source_bytes or not snapshot.source_matches(source_bytes):
            raise DataIntegrityError("calendar source checksum mismatch or empty source")
        if self._store is None:
            if any(item.version == snapshot.version for item in self._snapshots):
                raise DataIntegrityError("calendar version already registered")
            self._snapshots.append(snapshot)
            self._source_bytes[snapshot.version] = bytes(source_bytes)
            return
        payload = _calendar_payload(snapshot, source_bytes)
        try:
            inserted = self._store.append(
                namespace=self._namespace,
                identity=_calendar_identity(snapshot),
                payload=payload,
                payload_hash=_calendar_hash(payload),
                event="CALENDAR_SNAPSHOT_REGISTERED",
            )
        except ControlPlaneStoreError as exc:
            raise DataIntegrityError("calendar version conflict or storage failure") from exc
        if not inserted:
            raise DataIntegrityError("calendar version already registered")

    def _available_snapshots(self) -> list[CalendarSnapshot]:
        if self._store is None:
            for snapshot in self._snapshots:
                require_real_data(snapshot.data_kind.value, source=snapshot.source)
            return list(self._snapshots)
        try:
            payloads = self._store.list_latest(self._namespace)
            audits = self._store.audit(self._namespace)
            seen: set[str] = set()
            snapshots: list[CalendarSnapshot] = []
            for payload in payloads:
                snapshot = _calendar_from_payload(payload)
                identity = _calendar_identity(snapshot)
                events = [event for event in audits if event["identity"] == identity]
                if (
                    identity in seen
                    or self._store.get(self._namespace, identity) != payload
                    or len(events) != 1
                    or events[0]["event"] != "CALENDAR_SNAPSHOT_REGISTERED"
                    or events[0]["payload_hash"] != _calendar_hash(payload)
                ):
                    raise ValueError("calendar identity or audit mismatch")
                seen.add(identity)
                if (snapshot.exchange, snapshot.segment) == (self.exchange, self.segment):
                    require_real_data(snapshot.data_kind.value, source=snapshot.source)
                    snapshots.append(snapshot)
            # A missing newer record must not silently make an older revision
            # appear to be the latest available calendar. Audit entries belong
            # to this namespace across all exchanges, just like ``payloads``.
            if any(event["identity"] not in seen for event in audits):
                raise ValueError("calendar audit references a missing snapshot")
            return snapshots
        except (KeyError, TypeError, ValueError, binascii.Error) as exc:
            raise DataIntegrityError("calendar snapshot integrity check failed") from exc

    def snapshot_as_of(self, day: date, as_of: datetime) -> CalendarSnapshot:
        if as_of.utcoffset() is None:
            raise DataIntegrityError("calendar as_of must be timezone-aware")
        eligible = [
            item for item in self._available_snapshots()
            if item.coverage_start <= day <= item.coverage_end and item.available_at <= as_of
        ]
        if not eligible:
            raise DataIntegrityError("no sourced calendar available for date and as_of")
        latest = max(item.available_at for item in eligible)
        winners = [item for item in eligible if item.available_at == latest]
        if len(winners) != 1:
            raise DataIntegrityError("ambiguous calendar revisions at the same availability time")
        return winners[0]

    def session_as_of(self, day: date, as_of: datetime) -> tuple[datetime, datetime] | None:
        return self.snapshot_as_of(day, as_of).session(day)

    def bind(self, version: str, *, as_of: datetime) -> BoundCalendar:
        """Bind a registered revision to an existing TradingCalendar consumer."""
        snapshot = next(
            (item for item in self._available_snapshots() if item.version == version), None
        )
        if snapshot is None:
            raise DataIntegrityError("unknown calendar version")
        return BoundCalendar(snapshot, as_of=as_of)

    def source_bytes(self, version: str) -> bytes:
        """Return the exact stored source after checking snapshot and audit identity."""
        snapshot = next(
            (item for item in self._available_snapshots() if item.version == version), None
        )
        if snapshot is None:
            raise DataIntegrityError("unknown calendar version")
        if self._store is None:
            source = self._source_bytes.get(version)
            if source is None or not snapshot.source_matches(source):
                raise DataIntegrityError("calendar source integrity check failed")
            return source
        try:
            identity = _calendar_identity(snapshot)
            payload = self._store.get(self._namespace, identity)
            if payload is None or _calendar_from_payload(payload) != snapshot:
                raise ValueError("calendar snapshot changed while reading source")
            events = [
                event for event in self._store.audit(self._namespace)
                if event["identity"] == identity
            ]
            if (
                len(events) != 1
                or events[0]["event"] != "CALENDAR_SNAPSHOT_REGISTERED"
                or events[0]["payload_hash"] != _calendar_hash(payload)
            ):
                raise ValueError("calendar source audit mismatch")
            return base64.b64decode(str(payload["source_base64"]), validate=True)
        except (KeyError, TypeError, ValueError, binascii.Error) as exc:
            raise DataIntegrityError("calendar source integrity check failed") from exc


_CALENDAR_ADAPTER: TypeAdapter[CalendarSnapshot] = TypeAdapter(CalendarSnapshot)


def _calendar_identity(snapshot: CalendarSnapshot) -> str:
    return "".join(f"{len(value)}:{value}" for value in (
        snapshot.exchange, snapshot.segment, snapshot.version
    ))


def _calendar_hash(payload: dict[str, object]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()


def _calendar_payload(snapshot: CalendarSnapshot, source_bytes: bytes) -> dict[str, object]:
    data = _CALENDAR_ADAPTER.dump_python(snapshot, mode="json")
    data["holidays"] = sorted(data["holidays"])
    data["special_sessions"] = sorted(data["special_sessions"], key=lambda item: item["day"])
    return {
        "schema_version": 1,
        "snapshot": data,
        "source_base64": base64.b64encode(source_bytes).decode("ascii"),
    }


def _calendar_from_payload(payload: dict[str, object]) -> CalendarSnapshot:
    if set(payload) != {"schema_version", "snapshot", "source_base64"}:
        raise ValueError("invalid calendar payload fields")
    if payload["schema_version"] != 1 or not isinstance(payload["snapshot"], dict):
        raise ValueError("unsupported calendar payload")
    expected = set(CalendarSnapshot.__dataclass_fields__)
    if set(payload["snapshot"]) != expected:
        raise ValueError("invalid calendar snapshot fields")
    snapshot = _CALENDAR_ADAPTER.validate_python(payload["snapshot"])
    encoded = payload["source_base64"]
    if not isinstance(encoded, str):
        raise ValueError("invalid calendar source encoding")
    source = base64.b64decode(encoded, validate=True)
    if not source or not snapshot.source_matches(source):
        raise ValueError("calendar source checksum mismatch")
    return snapshot
