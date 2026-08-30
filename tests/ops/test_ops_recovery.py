from __future__ import annotations

import pytest

from quantlab.ops.errors import InvalidOpsTransition
from quantlab.ops.recovery import recover
from quantlab.ops.state import OpsState, force


def test_silent_recovery_forbidden() -> None:
    force(OpsState.HALTED)
    with pytest.raises(InvalidOpsTransition):
        recover(explicit=False)


def test_explicit_recovery_to_ready() -> None:
    force(OpsState.HALTED)
    assert recover(explicit=True) is OpsState.READY
