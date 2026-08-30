"""Session classification. Reuses Prompt 20 weekday calendar. No invented holidays."""

from __future__ import annotations

from datetime import datetime, timedelta

from quantlab.core.time import IST
from quantlab.data.fabric.calendar import WeekdayCalendar
from quantlab.realtime_data.models import SessionState

_calendar = WeekdayCalendar()


def classify(as_of: datetime, *, halted: bool = False) -> SessionState:
    if halted:
        return SessionState.HALTED
    local = as_of.astimezone(IST)
    day = local.date()
    if not _calendar.is_session(day):
        return SessionState.CLOSED
    open_t = _calendar.session_open(day)
    close_t = _calendar.session_close(day)
    pre = open_t - timedelta(minutes=15)
    closing = close_t - timedelta(minutes=15)
    if as_of < pre:
        return SessionState.CLOSED
    if as_of < open_t:
        return SessionState.PRE_OPEN
    if as_of < closing:
        return SessionState.OPEN
    if as_of < close_t:
        return SessionState.CLOSING
    return SessionState.CLOSED


def calendar_version() -> str:
    return _calendar.version
