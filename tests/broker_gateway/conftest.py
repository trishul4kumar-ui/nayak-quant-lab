from __future__ import annotations

import pytest

from quantlab.broker_gateway.service import reset_for_tests
from quantlab.core.config import LiveSafetyGates


@pytest.fixture(autouse=True)
def _reset_gateway() -> None:
    reset_for_tests()
    assert LiveSafetyGates().live_trading is False
    assert LiveSafetyGates().broker_write_enabled is False
