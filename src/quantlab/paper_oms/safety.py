"""Paper-only safety. Live, broker, and credential paths fail closed."""

from __future__ import annotations

import os

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


def assert_live_trading_disabled(*, live_trading: bool = False) -> None:
    gates = LiveSafetyGates()
    if live_trading or gates.live_trading:
        raise PaperSafetyError("paper OMS refuses to run while live_trading is true")
    assert live_trading is False
    assert gates.live_trading is False


def assert_no_broker_credentials() -> None:
    present = [name for name in FORBIDDEN_CREDENTIAL_VARS if os.environ.get(name)]
    if present:
        raise PaperSafetyError(
            "paper OMS fail-closed: broker/live credentials detected: " + ",".join(present)
        )


def assert_paper_only(*, live_trading: bool = False) -> None:
    assert_live_trading_disabled(live_trading=live_trading)
    assert_no_broker_credentials()
