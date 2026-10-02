"""Qt-safe production-shadow presentation boundary."""

from __future__ import annotations

from typing import Any

from quantlab.production_shadow.repository import last, state
from quantlab.production_shadow.service import assess

_LAST: dict[str, Any] | None = None


def run_payload() -> dict[str, Any]:
    result = assess()
    payload = result.model_dump(mode="json")
    global _LAST
    _LAST = payload
    return payload


def last_run_row() -> dict[str, Any] | None:
    return _LAST


def status_payload() -> dict[str, Any]:
    item = last()
    return {
        "state": state(),
        "critical_failures": list(item.readiness.critical_failures) if item else [],
        "live_trading": False,
        "broker_write_enabled": False,
    }
