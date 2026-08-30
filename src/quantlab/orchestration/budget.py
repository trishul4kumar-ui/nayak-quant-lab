"""Explicit research budgets. Exceeding a freeze is a FAIL, not a silent continue."""

from __future__ import annotations

from pydantic import BaseModel

from quantlab.orchestration.errors import OrchestrationError


class ResearchBudget(BaseModel):
    max_candidates: int = 8
    max_experiments: int = 16
    max_sign_flip_perm: int = 31

    def remaining_candidates(self, tested: int) -> int:
        return max(self.max_candidates - tested, 0)

    def remaining_experiments(self, ran: int) -> int:
        return max(self.max_experiments - ran, 0)


def apply_budget(
    n_generated: int,
    budget: ResearchBudget,
    *,
    bypass: bool = False,
) -> tuple[int, bool]:
    """Return (allowed_count, truncated). Bypass is an integrity FAIL."""
    if bypass:
        raise OrchestrationError("research budget bypass is prohibited")
    if n_generated <= budget.max_candidates:
        return n_generated, False
    return budget.max_candidates, True
