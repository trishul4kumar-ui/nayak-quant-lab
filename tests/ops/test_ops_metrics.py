from __future__ import annotations

import pytest

from quantlab.core.config import LiveSafetyGates
from quantlab.ops.errors import OpsError
from quantlab.ops.scheduler import run_job


def test_scheduler_cannot_invoke_live_trading() -> None:
    assert LiveSafetyGates().live_trading is False
    with pytest.raises(OpsError):
        run_job("live")
    assert run_job("research") == "research"
