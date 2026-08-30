"""Annualization conventions. Do not scatter sqrt(252) through research code."""

from __future__ import annotations

import math
from datetime import date

from pydantic import BaseModel

from quantlab.data.fabric.calendar import WeekdayCalendar


class Annualization(BaseModel):
    """How periodic statistics are scaled to a year.

    risk_free_rate defaults to 0. That is an explicit convention, not an Indian T-bill.
    """

    sessions_per_year: int = 252
    provenance: str = "weekday_sessions_not_official_nse_holidays"
    risk_free_rate: float = 0.0
    risk_free_convention: str = "zero_explicit_not_indian_t_bill"
    schema_version: str = "1"

    def sqrt_sessions(self) -> float:
        if self.sessions_per_year <= 0:
            raise ValueError("sessions_per_year must be positive")
        return math.sqrt(float(self.sessions_per_year))


DEFAULT_ANNUALIZATION = Annualization()


def sessions_per_year(calendar: WeekdayCalendar, year: int = 2024) -> int:
    """Count weekday sessions in a calendar year. Not an official NSE holiday count."""
    start = date(year, 1, 1)
    end = date(year, 12, 31)
    return max(len(calendar.sessions(start, end)), 1)
