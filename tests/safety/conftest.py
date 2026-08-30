from __future__ import annotations

import pytest

from quantlab.core.config import LiveSafetyGates
from quantlab.safety.service import reset_for_tests


@pytest.fixture(autouse=True)
def _reset_safety() -> None:
    reset_for_tests()
    gates = LiveSafetyGates()
    assert gates.live_trading is False
    assert gates.broker_routing_enabled is False
    assert gates.live_order_submission_enabled is False
