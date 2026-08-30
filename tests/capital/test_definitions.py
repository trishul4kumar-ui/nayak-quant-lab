from __future__ import annotations

import pytest

from quantlab.capital.definitions import CapitalAllocationState, DecisionStatus
from quantlab.capital.library import seed_policy

pytestmark = pytest.mark.capital


def test_policy_hash_is_stable() -> None:
    a = seed_policy()
    b = seed_policy()
    assert a.config_hash
    assert a.config_hash == b.config_hash
    assert a.kelly_fraction == 0.25
    assert a.base_currency == "INR"


def test_decision_status_has_no_live_states() -> None:
    names = {item.name for item in DecisionStatus}
    assert "LIVE_READY" not in names
    assert "LIVE_APPROVED" not in names
    assert "LIVE_ORDERED" not in names
    assert "RESEARCH_ONLY" in names


def test_allocation_states_are_policy_driven() -> None:
    assert {item.value for item in CapitalAllocationState} == {
        "full",
        "reduced",
        "defensive",
        "abstain",
        "halt",
    }
