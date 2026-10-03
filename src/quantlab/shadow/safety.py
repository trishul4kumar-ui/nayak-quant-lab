"""Shadow-only safety. Live, broker, and credential paths fail closed."""

from __future__ import annotations

import os

from quantlab.core.config import LiveSafetyGates
from quantlab.core.errors import LiveRouteAttempt, SafetyError, ShadowError

FORBIDDEN_CREDENTIAL_VARS = (
    "BROKER_PASSWORD",
    "LIVE_ACCOUNT_ID",
    "LIVE_ORDER_TOKEN",
    "API_KEY",
    "API_SECRET",
    "ACCESS_TOKEN",
    "KITE_API_KEY",
    "KITE_API_SECRET",
    "ZERODHA_API_KEY",
    "OPENALGO_API_KEY",
)


def assert_live_trading_disabled(*, live_trading: bool = False) -> LiveSafetyGates:
    gates = LiveSafetyGates()
    if live_trading or gates.live_trading or gates.live_trading_enabled:
        raise SafetyError("shadow engine refuses to run while live_trading is true")
    if gates.broker_routing_enabled or gates.live_order_submission_enabled:
        raise LiveRouteAttempt("shadow engine refuses broker routing flags")
    return gates


def assert_no_broker_credentials() -> None:
    present = [name for name in FORBIDDEN_CREDENTIAL_VARS if os.environ.get(name)]
    if present:
        raise ShadowError(
            "shadow fail-closed: broker/live credentials detected: " + ",".join(present)
        )


def assert_no_live_route(*, route_live: bool = False) -> None:
    if route_live:
        raise LiveRouteAttempt("live broker route requested on the shadow path")


def assert_no_ai_override(*, ai_override: bool = False) -> None:
    if ai_override:
        raise ShadowError("AI_SUGGESTION cannot override safety, certification, or routing")


def assert_shadow_only(*, live_trading: bool = False, route_live: bool = False) -> LiveSafetyGates:
    gates = assert_live_trading_disabled(live_trading=live_trading)
    assert_no_broker_credentials()
    assert_no_live_route(route_live=route_live)
    return gates
