"""Source-backed exchange-session classification for the daily desk."""

from __future__ import annotations

from datetime import datetime, time

from quantlab.agent_desk.models import DeskSession
from quantlab.core.time import IST
from quantlab.data.fabric.calendar import SourcedCalendar, TradingCalendar

_OPEN = time(9, 15)
_OPENING_END = time(9, 30)
_CLOSING_START = time(15, 15)
_CLOSE = time(15, 30)


def require_sourced_calendar(calendar: TradingCalendar) -> SourcedCalendar:
    """Reject the weekday fallback: it is not an official exchange calendar."""
    if not isinstance(calendar, SourcedCalendar):
        raise ValueError("CANONICAL_SOURCED_CALENDAR_REQUIRED")
    return calendar


def classify_session(when: datetime, calendar: TradingCalendar) -> DeskSession:
    require_sourced_calendar(calendar)
    local = when.astimezone(IST)
    if not calendar.is_session(local.date()):
        return DeskSession.CLOSED
    current = local.timetz().replace(tzinfo=None)
    if current < _OPEN:
        return DeskSession.PRE_MARKET
    if current < _OPENING_END:
        return DeskSession.OPENING
    if current < _CLOSING_START:
        return DeskSession.CONTINUOUS
    if current < _CLOSE:
        return DeskSession.CLOSING
    return DeskSession.POST_MARKET
