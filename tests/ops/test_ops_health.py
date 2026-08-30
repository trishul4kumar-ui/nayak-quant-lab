from __future__ import annotations

from quantlab.ops.service import integrate_safety_halt
from quantlab.ops.state import OpsState, current


def test_safety_halt_integration_works() -> None:
    result = integrate_safety_halt()
    assert current() is OpsState.SAFETY_FAILURE
    assert result.state is OpsState.SAFETY_FAILURE
    assert any(item.kind == "safety_halt_failure" for item in result.incidents)
