from __future__ import annotations

import pytest

from quantlab.ops.errors import InvalidOpsTransition
from quantlab.ops.state import FATAL, OpsState, current, force, transition


def test_fatal_cannot_auto_return_to_running() -> None:
    force(OpsState.CONFIG_INVALID)
    with pytest.raises(InvalidOpsTransition):
        transition(OpsState.RUNNING)
    assert current() is OpsState.CONFIG_INVALID
    assert OpsState.CONFIG_INVALID in FATAL
