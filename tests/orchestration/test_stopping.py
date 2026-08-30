from __future__ import annotations

import pytest

from quantlab.orchestration.contracts import StoppingPolicy
from quantlab.orchestration.errors import OrchestrationError
from quantlab.orchestration.stopping import StoppingRule, assert_not_posthoc


@pytest.mark.orchestration
def test_posthoc_stopping_is_rejected() -> None:
    rule = StoppingRule(policy=StoppingPolicy.PRE_REGISTERED_BUDGET, max_candidates=4)
    assert rule.should_stop(4)
    with pytest.raises(OrchestrationError, match="post-hoc"):
        assert_not_posthoc(rule, mutated_after_results=True)
    with pytest.raises(OrchestrationError, match="post-hoc"):
        assert_not_posthoc(StoppingRule(policy=StoppingPolicy.POSTHOC), mutated_after_results=False)
