from __future__ import annotations

import pytest

from quantlab.orchestration.contracts import ResearchStatus
from quantlab.orchestration.errors import OrchestrationError
from quantlab.orchestration.status import can_transition, transition


@pytest.mark.orchestration
def test_status_transitions_are_validated() -> None:
    assert can_transition(ResearchStatus.DRAFT, ResearchStatus.REGISTERED)
    assert transition(ResearchStatus.PLANNED, ResearchStatus.RUNNING) is ResearchStatus.RUNNING
    with pytest.raises(OrchestrationError, match="illegal"):
        transition(ResearchStatus.SUPERSEDED, ResearchStatus.RUNNING)
    with pytest.raises(OrchestrationError, match="illegal"):
        transition(ResearchStatus.RUNNING, ResearchStatus.DRAFT)
