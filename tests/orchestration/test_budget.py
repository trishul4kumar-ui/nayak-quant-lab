from __future__ import annotations

import pytest

from quantlab.orchestration.budget import ResearchBudget, apply_budget
from quantlab.orchestration.errors import OrchestrationError


@pytest.mark.orchestration
def test_budget_truncates_and_bypass_fails() -> None:
    allowed, truncated = apply_budget(10, ResearchBudget(max_candidates=3))
    assert allowed == 3
    assert truncated is True
    with pytest.raises(OrchestrationError, match="bypass"):
        apply_budget(10, ResearchBudget(max_candidates=3), bypass=True)
