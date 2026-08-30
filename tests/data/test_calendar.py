from datetime import date

import pytest

from quantlab.core.errors import DataIntegrityError
from quantlab.core.time import IST
from quantlab.data.fabric.calendar import WeekdayCalendar, calendar_from_sessions, session_date_ist
from quantlab.data.fabric.csvio import parse_timestamp


def test_weekday_calendar_is_not_official_nse() -> None:
    cal = WeekdayCalendar()
    assert "not_official" in cal.provenance
    assert cal.is_session(date(2024, 1, 26)) is True


def test_calendar_from_observed_sessions() -> None:
    sessions = [date(2024, 1, 2), date(2024, 1, 3), date(2024, 1, 5)]
    cal = calendar_from_sessions(sessions)
    assert cal.provenance == "derived_from_observed_bar_sessions"
    assert cal.is_session(date(2024, 1, 4)) is False


def test_date_only_uses_session_close_ist() -> None:
    cal = WeekdayCalendar()
    value, convention = parse_timestamp("2024-01-02", cal)
    assert convention == "session_close"
    assert session_date_ist(value) == date(2024, 1, 2)
    assert value.astimezone(IST).hour == 15
    assert value.astimezone(IST).minute == 30


def test_naive_datetime_rejected() -> None:
    with pytest.raises(DataIntegrityError):
        parse_timestamp("2024-01-02 15:30:00", WeekdayCalendar())
