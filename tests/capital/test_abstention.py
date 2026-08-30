from __future__ import annotations

import pytest

from quantlab.capital.allocator import allocate
from quantlab.capital.definitions import AbstentionCode, DecisionStatus
from quantlab.capital.library import seed_request
from quantlab.research.gate import GateOutcome, ResearchGateResult

pytestmark = pytest.mark.capital


def test_gate_fail_prohibits_allocation() -> None:
    request = seed_request().model_copy(
        update={"gate": ResearchGateResult(outcome=GateOutcome.REJECT)}
    )
    result = allocate(request)
    assert result.decision.decision_status is DecisionStatus.REJECTED
    assert result.decision.abstention_code is AbstentionCode.GATE_FAIL
    assert result.decision.target_weights == {}


def test_synthetic_cannot_promote_to_paper() -> None:
    request = seed_request().model_copy(
        update={"gate": ResearchGateResult(outcome=GateOutcome.PROMOTED_TO_PAPER)}
    )
    result = allocate(request)
    assert result.decision.decision_status is DecisionStatus.RESEARCH_ONLY
    assert result.decision.decision_status is not DecisionStatus.PAPER_READY
