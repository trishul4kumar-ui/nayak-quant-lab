from __future__ import annotations

import pytest

from quantlab.orchestration.errors import OrchestrationError
from quantlab.orchestration.hypothesis import HypothesisSpec
from quantlab.orchestration.registry import OrchestrationRegistry, get_hypothesis


@pytest.mark.orchestration
def test_registry_refuses_overwrite() -> None:
    store = OrchestrationRegistry()
    spec = HypothesisSpec(
        hypothesis_id="H-TEST-001",
        title="t",
        description="d",
    )
    store.register_hypothesis(spec)
    with pytest.raises(OrchestrationError, match="overwrite"):
        store.register_hypothesis(spec)


@pytest.mark.orchestration
def test_seed_hypothesis_is_registered() -> None:
    assert get_hypothesis("H-MOM-001").title
