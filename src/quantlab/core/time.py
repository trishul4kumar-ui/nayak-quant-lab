"""Clocks and point-in-time stamps. Never use datetime.now() in research code."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field, model_validator

IST = ZoneInfo("Asia/Kolkata")


class Clock(Protocol):
    def now(self) -> datetime: ...


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(tz=UTC)


class FrozenClock:
    def __init__(self, when: datetime) -> None:
        if when.tzinfo is None:
            raise ValueError("clock time must be timezone-aware")
        self._when = when

    def now(self) -> datetime:
        return self._when


class PointInTime(BaseModel):
    """When the fact happened vs when a researcher could have known it."""

    event_time: datetime
    effective_time: datetime
    available_time: datetime
    ingestion_time: datetime = Field(default_factory=lambda: datetime.now(tz=UTC))

    @model_validator(mode="after")
    def _aware(self) -> PointInTime:
        for name in ("event_time", "effective_time", "available_time", "ingestion_time"):
            value = getattr(self, name)
            if value.tzinfo is None:
                raise ValueError(f"{name} must be timezone-aware")
        if self.available_time < self.event_time:
            raise ValueError("available_time cannot precede event_time")
        return self

    def is_available_at(self, as_of: datetime) -> bool:
        return self.available_time <= as_of


def as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("naive datetime rejected")
    return value.astimezone(UTC)
