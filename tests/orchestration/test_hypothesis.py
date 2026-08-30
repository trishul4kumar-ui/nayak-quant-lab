from __future__ import annotations

import pytest

from quantlab.orchestration.errors import OrchestrationError
from quantlab.orchestration.hypothesis import assert_frozen
from quantlab.orchestration.registry import get_hypothesis


@pytest.mark.orchestration
def test_hypothesis_identity_is_stable() -> None:
    a = get_hypothesis("H-MOM-001")
    b = get_hypothesis("H-MOM-001")
    assert a.identity_hash() == b.identity_hash()
    assert a.hypothesis_id == "H-MOM-001"


@pytest.mark.orchestration
def test_hypothesis_mutation_changes_hash() -> None:
    spec = get_hypothesis("H-MOM-001")
    mutated = spec.model_copy(update={"description": "changed after freeze"})
    assert spec.identity_hash() != mutated.identity_hash()
    with pytest.raises(OrchestrationError):
        assert_frozen(spec, mutated)
