"""Pre-registered stopping. Peeking at results to stop is a leak."""

from __future__ import annotations

from pydantic import BaseModel

from quantlab.orchestration.contracts import StoppingPolicy
from quantlab.orchestration.errors import OrchestrationError


class StoppingRule(BaseModel):
    policy: StoppingPolicy = StoppingPolicy.PRE_REGISTERED_BUDGET
    max_candidates: int = 8
    frozen: bool = True

    def should_stop(self, tested: int) -> bool:
        return tested >= self.max_candidates


def assert_not_posthoc(rule: StoppingRule, *, mutated_after_results: bool) -> None:
    if mutated_after_results or rule.policy is StoppingPolicy.POSTHOC:
        raise OrchestrationError("post-hoc stopping after seeing results is prohibited")
    if not rule.frozen:
        raise OrchestrationError("stopping rule must be frozen before execution")
