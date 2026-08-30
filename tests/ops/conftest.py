from __future__ import annotations

import pytest

from quantlab.core.config import LiveSafetyGates
from quantlab.ops.service import reset_for_tests


@pytest.fixture(autouse=True)
def _reset_ops() -> None:
    reset_for_tests()
    assert LiveSafetyGates().live_trading is False
