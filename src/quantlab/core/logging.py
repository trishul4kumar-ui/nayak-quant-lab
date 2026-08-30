"""Structured logging. No secrets in log fields."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

import structlog

LogSink = Callable[[dict[str, Any]], None]


def configure_logging(level: str = "INFO", sink: LogSink | None = None) -> None:
    def attach_sink(
        _logger: object, method_name: str, event_dict: dict[str, Any]
    ) -> dict[str, Any]:
        if sink is not None:
            payload = dict(event_dict)
            payload.setdefault("level", method_name)
            sink(payload)
        return event_dict

    processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        attach_sink,
        structlog.processors.JSONRenderer(),
    ]
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, level.upper(), logging.INFO)
        ),
        logger_factory=structlog.PrintLoggerFactory(),
    )


def get_logger(name: str, **initial: Any) -> Any:
    return structlog.get_logger(name).bind(**initial)
