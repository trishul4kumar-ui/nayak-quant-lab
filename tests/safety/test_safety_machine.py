from __future__ import annotations

import pytest

from quantlab.safety.errors import InvalidSafetyTransition
from quantlab.safety.state import SafetyState, current, reset_for_tests, transition


@pytest.mark.parametrize(
    ("source", "target"),
    [
        (SafetyState.RESEARCH_ONLY, SafetyState.AUTHORIZED),
        (SafetyState.PAPER, SafetyState.AUTHORIZED),
        (SafetyState.HALTED, SafetyState.AUTHORIZED),
        (SafetyState.EMERGENCY, SafetyState.AUTHORIZED),
        (SafetyState.DISABLED, SafetyState.ARMED),
        (SafetyState.RECOVERY_PENDING, SafetyState.AUTHORIZED),
    ],
)
def test_illegal_transitions(source: SafetyState, target: SafetyState) -> None:
    reset_for_tests()
    from quantlab.safety.state import force

    force(source)
    with pytest.raises(InvalidSafetyTransition):
        transition(target)
    assert current() is source


def test_legal_shadow_to_armed() -> None:
    from quantlab.safety.state import force

    force(SafetyState.SHADOW)
    assert transition(SafetyState.ARMED) is SafetyState.ARMED
