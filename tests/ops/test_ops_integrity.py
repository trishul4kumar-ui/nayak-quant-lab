from __future__ import annotations

from pathlib import Path

from quantlab.core.config import LiveSafetyGates


def test_no_broker_imports() -> None:
    root = Path("src/quantlab/ops")
    banned = ("kiteconnect", "zerodha", "openalgo", "quantlab.brokers")
    for path in root.rglob("*.py"):
        text = path.read_text()
        for token in banned:
            assert token not in text


def test_live_trading_false_remains_enforced() -> None:
    gates = LiveSafetyGates()
    assert gates.live_trading is False
    assert gates.broker_routing_enabled is False
    assert gates.live_order_submission_enabled is False
