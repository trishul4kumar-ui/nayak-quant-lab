"""Fundamental observations. period_end is not available_time. Revisions are append-only."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, model_validator


class FundamentalObservation(BaseModel):
    security_id: str
    metric: str
    value: float
    period_start: date
    period_end: date
    publication_time: datetime
    available_time: datetime
    source: str
    revision: int = 1

    @model_validator(mode="after")
    def _period_is_not_availability(self) -> FundamentalObservation:
        if self.available_time.tzinfo is None or self.publication_time.tzinfo is None:
            raise ValueError("fundamental timestamps must be timezone-aware")
        return self


class FundamentalStore:
    def __init__(self) -> None:
        self._rows: list[FundamentalObservation] = []

    def add(self, row: FundamentalObservation) -> None:
        self._rows.append(row)

    def as_of(
        self,
        security_id: str,
        metric: str,
        as_of: datetime,
    ) -> FundamentalObservation | None:
        eligible = [
            row
            for row in self._rows
            if row.security_id == security_id
            and row.metric == metric
            and row.available_time <= as_of
        ]
        if not eligible:
            return None
        eligible.sort(key=lambda r: (r.available_time, r.revision))
        return eligible[-1]
