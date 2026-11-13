"""Paper-only safety. Live, broker, and credential paths fail closed."""

from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar

from quantlab.core.config import LiveSafetyGates
from quantlab.paper_oms.errors import PaperSafetyError

FORBIDDEN_CREDENTIAL_VARS = (
    "API_KEY",
    "API_SECRET",
    "ACCESS_TOKEN",
    "BROKER_PASSWORD",
    "LIVE_ACCOUNT_ID",
    "KITE_API_KEY",
    "KITE_API_SECRET",
    "ZERODHA_API_KEY",
    "OPENALGO_API_KEY",
)

_SOURCED_SIMULATION: ContextVar[str | None] = ContextVar("sourced_paper_simulation", default=None)
_OBSERVATION_ENV = frozenset({"KITE_API_KEY", "KITE_API_SECRET", "ZERODHA_API_KEY"})


@contextmanager
def sourced_simulation_scope(workflow_hash: str) -> Iterator[None]:
    """A verified local-data workflow receives simulation capability, never a client.

    Environment credentials are neither read nor forwarded to the simulator.
    This context is thread-local, cannot change global environment or safety
    flags, and is entered only after the original input bundle is verified.
    """
    if len(workflow_hash) != 64 or any(c not in "0123456789abcdef" for c in workflow_hash):
        raise PaperSafetyError("VERIFIED_WORKFLOW_ID_REQUIRED")
    token = _SOURCED_SIMULATION.set(workflow_hash)
    try:
        assert_live_trading_disabled()
        yield
    finally:
        _SOURCED_SIMULATION.reset(token)


def isolated_observation_credentials() -> frozenset[str]:
    """Only source-specific observation configuration may coexist in this scope."""
    return _OBSERVATION_ENV if _SOURCED_SIMULATION.get() is not None else frozenset()


def assert_live_trading_disabled(*, live_trading: bool = False) -> None:
    gates = LiveSafetyGates()
    if (
        live_trading
        or gates.live_trading
        or gates.live_trading_enabled
        or gates.broker_write_enabled
        or gates.broker_routing_enabled
        or gates.live_order_submission_enabled
    ):
        raise PaperSafetyError("paper OMS refuses to run while live_trading is true")


def assert_no_broker_credentials() -> None:
    isolated = isolated_observation_credentials()
    present = [
        name for name in FORBIDDEN_CREDENTIAL_VARS if name not in isolated and os.environ.get(name)
    ]
    if present:
        raise PaperSafetyError(
            "paper OMS fail-closed: broker/live credentials detected: " + ",".join(present)
        )


def assert_paper_only(*, live_trading: bool = False) -> None:
    assert_live_trading_disabled(live_trading=live_trading)
    assert_no_broker_credentials()
