from __future__ import annotations

import pytest

from quantlab.core.config import LiveSafetyGates
from quantlab.release.service import reset_for_tests


@pytest.fixture(autouse=True)
def _reset_release() -> None:
    reset_for_tests()
    assert LiveSafetyGates().live_trading is False
    assert LiveSafetyGates().broker_write_enabled is False
