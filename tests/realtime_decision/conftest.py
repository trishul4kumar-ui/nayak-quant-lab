from __future__ import annotations

import pytest

from quantlab.core.config import LiveSafetyGates
from quantlab.realtime_decision.service import reset_for_tests


@pytest.fixture(autouse=True)
def _reset_decision() -> None:
    from quantlab.realtime_data.service import reset_for_tests as reset_data

    reset_data()
    reset_for_tests()
    assert LiveSafetyGates().live_trading is False
    assert LiveSafetyGates().broker_write_enabled is False
