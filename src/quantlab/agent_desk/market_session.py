"""Source-backed exchange-session classification for the daily desk."""

from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from quantlab.agent_desk.models import DeskSession
from quantlab.data.fabric.calendar import SourcedCalendar, TradingCalendar

_PHASE_WINDOW = timedelta(minutes=15)


def require_sourced_calendar(calendar: TradingCalendar) -> SourcedCalendar:
    """Reject the weekday fallback: it is not an official exchange calendar."""
    if not isinstance(calendar, SourcedCalendar):
        raise ValueError("CANONICAL_SOURCED_CALENDAR_REQUIRED")
    return calendar


def classify_session(when: datetime, calendar: TradingCalendar) -> DeskSession:
    source = require_sourced_calendar(calendar)
    if when.utcoffset() is None:
        raise ValueError("SESSION_TIME_MUST_BE_AWARE")
    local = when.astimezone(ZoneInfo(source.timezone))
    if not calendar.is_session(local.date()):
        return DeskSession.CLOSED
    opening = calendar.session_open(local.date())
    closing = calendar.session_close(local.date())
    if when < opening:
        return DeskSession.PRE_MARKET
    if when >= closing:
        return DeskSession.POST_MARKET
    if when < min(opening + _PHASE_WINDOW, closing):
        return DeskSession.OPENING
    if when < closing - _PHASE_WINDOW:
        return DeskSession.CONTINUOUS
    return DeskSession.CLOSING
