"""Market session wrapping Prompt 20's weekday calendar. Never invents NSE holidays."""

from __future__ import annotations

from datetime import datetime

from quantlab.core.time import IST
from quantlab.data.fabric.calendar import WeekdayCalendar
from quantlab.domain.research import CheckResult
from quantlab.shadow.enums import SessionState

_OPEN = (9, 15)
_CLOSE = (15, 30)


def session_state(
    when: datetime,
    *,
    calendar: WeekdayCalendar | None = None,
    override: SessionState | None = None,
) -> tuple[SessionState, CheckResult]:
    if override is not None:
        return override, CheckResult.NOT_TESTED
    cal = calendar or WeekdayCalendar()
    local = when.astimezone(IST)
    day = local.date()
    if not cal.is_session(day):
        return SessionState.HOLIDAY, CheckResult.NOT_TESTED
    hour, minute = local.hour, local.minute
    open_min = _OPEN[0] * 60 + _OPEN[1]
    close_min = _CLOSE[0] * 60 + _CLOSE[1]
    now_min = hour * 60 + minute
    if now_min < open_min:
        return SessionState.PRE_OPEN, CheckResult.NOT_TESTED
    if now_min >= close_min:
        return SessionState.POST_CLOSE, CheckResult.NOT_TESTED
    return SessionState.CONTINUOUS, CheckResult.NOT_TESTED


def is_tradable(state: SessionState) -> bool:
    return state in {SessionState.OPEN, SessionState.CONTINUOUS}
