"""In-process typed events. Domain does not depend on a broker."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class EventType(StrEnum):
    MARKET = "market"
    TICK = "tick"
    BAR = "bar"
    FUNDAMENTAL = "fundamental"
    NEWS = "news"
    DATA = "data"
    FEATURE = "feature"
    SIGNAL = "signal"
    MODEL = "model"
    PORTFOLIO = "portfolio"
    RISK = "risk"
    ORDER = "order"
    EXECUTION = "execution"
    FILL = "fill"
    EXPERIMENT = "experiment"
    RESEARCH = "research"
    SYSTEM = "system"
    ALERT = "alert"


class Event(BaseModel):
    type: EventType
    correlation_id: str = ""
    component: str = ""
    payload: dict[str, Any] = Field(default_factory=dict)


Handler = Callable[[Event], None]


class EventBus:
    def __init__(self) -> None:
        self._handlers: dict[EventType, list[Handler]] = defaultdict(list)

    def subscribe(self, event_type: EventType, handler: Handler) -> None:
        self._handlers[event_type].append(handler)

    def publish(self, event: Event) -> None:
        for handler in self._handlers.get(event.type, []):
            handler(event)
