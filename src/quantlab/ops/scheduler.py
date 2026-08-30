"""Ops scheduler. Cannot invoke live trading."""

from __future__ import annotations

from quantlab.core.config import LiveSafetyGates
from quantlab.ops.errors import OpsError


def run_job(name: str) -> str:
    if LiveSafetyGates().live_trading:
        raise OpsError("scheduler cannot invoke live trading")
    if name in {"live", "broker_submit", "release_live"}:
        raise OpsError("scheduler cannot invoke live trading")
    return name
