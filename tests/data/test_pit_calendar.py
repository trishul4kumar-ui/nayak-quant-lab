from __future__ import annotations

from dataclasses import replace
from datetime import UTC, date, datetime, time
from hashlib import sha256

import pytest

from quantlab.core.errors import DataIntegrityError
from quantlab.data.fabric.calendar import CalendarSnapshot, PointInTimeCalendar, SessionOverride
from quantlab.data.fabric.csvio import parse_timestamp

RAW = b"calendar source revision one"
JAN = date(2024, 1, 1)
DAY = date(2024, 1, 26)


def snapshot(**changes: object) -> CalendarSnapshot:
    values: dict[str, object] = {
        "exchange": "NSE", "segment": "CM", "version": "v1", "source": "fixture",
        "source_sha256": sha256(RAW).hexdigest(),
        "published_at": datetime(2023, 12, 1, tzinfo=UTC),
        "available_at": datetime(2023, 12, 2, tzinfo=UTC),
        "coverage_start": JAN, "coverage_end": date(2024, 12, 31),
        "timezone": "Asia/Kolkata", "regular_open": time(9, 15),
        "regular_close": time(15, 30), "holidays": frozenset({DAY}),
    }
    values.update(changes)
    return CalendarSnapshot(**values)  # type: ignore[arg-type]


def test_revisions_do_not_leak_before_availability() -> None:
    calendar = PointInTimeCalendar(exchange="NSE", segment="CM")
    original = snapshot()
    revision = replace(
        original, version="v2", holidays=frozenset(),
        published_at=datetime(2024, 1, 20, tzinfo=UTC),
        available_at=datetime(2024, 1, 21, tzinfo=UTC),
    )
    calendar.add(original, source_bytes=RAW)
    calendar.add(revision, source_bytes=RAW)
    assert calendar.session_as_of(DAY, datetime(2024, 1, 20, tzinfo=UTC)) is None
    opened, closed = calendar.session_as_of(DAY, datetime(2024, 1, 21, tzinfo=UTC)) or ()
    assert opened == datetime(2024, 1, 26, 3, 45, tzinfo=UTC)
    assert closed == datetime(2024, 1, 26, 10, 0, tzinfo=UTC)


def test_special_weekend_and_shortened_session_use_explicit_hours() -> None:
    saturday = date(2024, 1, 6)
    special = SessionOverride(saturday, time(10), time(12))
    item = snapshot(special_sessions=(special,))
    calendar = PointInTimeCalendar(exchange="NSE", segment="CM")
    calendar.add(item, source_bytes=RAW)
    assert calendar.session_as_of(saturday, datetime(2024, 1, 2, tzinfo=UTC)) == (
        datetime(2024, 1, 6, 4, 30, tzinfo=UTC), datetime(2024, 1, 6, 6, 30, tzinfo=UTC)
    )
    assert calendar.session_as_of(date(2024, 1, 7), datetime(2024, 1, 2, tzinfo=UTC)) is None


def test_missing_future_or_uncovered_reference_is_never_guessed() -> None:
    calendar = PointInTimeCalendar(exchange="NSE", segment="CM")
    calendar.add(snapshot(), source_bytes=RAW)
    for day, cutoff in (
        (DAY, datetime(2023, 12, 1, tzinfo=UTC)),
        (date(2025, 1, 1), datetime(2024, 3, 1, tzinfo=UTC)),
        (DAY, datetime(2024, 1, 1)),
    ):
        with pytest.raises(DataIntegrityError):
            calendar.session_as_of(day, cutoff)


def test_bad_source_collision_and_ambiguous_revisions_are_rejected() -> None:
    calendar = PointInTimeCalendar(exchange="NSE", segment="CM")
    with pytest.raises(DataIntegrityError, match="checksum"):
        calendar.add(snapshot(), source_bytes=b"wrong bytes")
    calendar.add(snapshot(), source_bytes=RAW)
    with pytest.raises(DataIntegrityError, match="version"):
        calendar.add(snapshot(), source_bytes=RAW)
    calendar.add(snapshot(version="v2"), source_bytes=RAW)
    with pytest.raises(DataIntegrityError, match="ambiguous"):
        calendar.session_as_of(DAY, datetime(2024, 1, 1, tzinfo=UTC))


def test_bound_view_works_with_existing_calendar_consumer_and_rejects_closed_days() -> None:
    calendar = PointInTimeCalendar(exchange="NSE", segment="CM")
    calendar.add(snapshot(), source_bytes=RAW)
    view = calendar.bind("v1", as_of=datetime(2024, 1, 1, tzinfo=UTC))
    assert parse_timestamp("2024-01-02", view)[0] == datetime(2024, 1, 2, 10, tzinfo=UTC)
    assert view.version == "v1"
    with pytest.raises(DataIntegrityError, match="not a trading session"):
        view.session_close(DAY)
    with pytest.raises(DataIntegrityError, match="unavailable"):
        calendar.bind("v1", as_of=datetime(2023, 1, 1, tzinfo=UTC))


def test_ambiguous_dst_hours_are_not_guessed() -> None:
    item = snapshot(
        timezone="America/New_York", holidays=frozenset(),
        special_sessions=(SessionOverride(date(2024, 11, 3), time(1, 30), time(3)),),
    )
    with pytest.raises(DataIntegrityError, match="ambiguous or nonexistent"):
        item.session(date(2024, 11, 3))


def test_inconsistent_source_and_session_definitions_are_rejected() -> None:
    with pytest.raises(ValueError, match="publication"):
        snapshot(available_at=datetime(2023, 11, 1, tzinfo=UTC))
    with pytest.raises(ValueError, match="both a holiday"):
        snapshot(special_sessions=(SessionOverride(DAY, time(9), time(10)),))
    with pytest.raises(ValueError, match="coverage"):
        snapshot(holidays=frozenset({date(2025, 1, 1)}))
