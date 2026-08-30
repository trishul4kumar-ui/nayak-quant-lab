from __future__ import annotations

from datetime import UTC, datetime

import pytest

from quantlab.data.fabric.calendar import WeekdayCalendar
from quantlab.data.market_data import get as market_get
from quantlab.data.provenance import provenance_from_bytes
from quantlab.data.snapshots import freeze_snapshot
from tests.data.helpers import make_bar, utc_day


@pytest.mark.parametrize("year", [2020, 2021, 2022, 2023, 2024])
@pytest.mark.parametrize("month", [1, 6, 12])
def test_pit_across_calendar_grid(year: int, month: int) -> None:
    as_of = utc_day(year, month, 15)
    future = utc_day(year + 1, month, 15) if month != 12 else utc_day(year + 1, 1, 15)
    bars = [make_bar("AAA", as_of, close=10.0), make_bar("AAA", future, close=99.0)]
    got = market_get(as_of=as_of, bars=bars)
    assert all(bar.pit.available_time <= as_of for bar in got)
    assert all(bar.close != 99.0 for bar in got)


@pytest.mark.parametrize("src", ["user-csv", "licensed-dump", "synthetic-fixture"])
def test_provenance_sources(src: str) -> None:
    row = provenance_from_bytes(b"x", dataset_id="d", version="v1", source=src)
    assert row.source == src


@pytest.mark.parametrize("dep", ["calendar_version", "universe_version", "dataset_checksum"])
def test_snapshot_dependency_identity(dep: str) -> None:
    a = freeze_snapshot(**{dep: "a"})
    b = freeze_snapshot(**{dep: "b"})
    assert a.snapshot_hash != b.snapshot_hash


@pytest.mark.parametrize("weekday", range(7))
def test_weekday_calendar_weekend(weekday: int) -> None:
    cal = WeekdayCalendar()
    day = datetime(2024, 1, 1, tzinfo=UTC).date()  # Monday
    from datetime import timedelta

    probe = day + timedelta(days=weekday)
    assert cal.is_session(probe) is (weekday < 5)


@pytest.mark.parametrize("close", [1.0, 10.0, 100.0, 2500.0])
def test_get_preserves_close(close: float) -> None:
    day = utc_day(2024, 1, 15)
    bars = [make_bar("AAA", day, close=close)]
    got = market_get(as_of=day, bars=bars)
    assert got[0].close == close
