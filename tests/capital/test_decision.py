from __future__ import annotations

import pytest
from pydantic import ValidationError

from quantlab.capital.allocator import allocate
from quantlab.capital.decision import mutate_decision
from quantlab.capital.errors import CapitalError
from quantlab.capital.library import seed_request

pytestmark = pytest.mark.capital


def test_decision_is_frozen() -> None:
    result = allocate(seed_request())
    with pytest.raises(ValidationError):
        result.decision.decision_status = "paper_ready"  # type: ignore[misc]


def test_mutate_helper_refuses() -> None:
    result = allocate(seed_request())
    with pytest.raises(CapitalError, match="decision_mutation"):
        mutate_decision(result.decision, decision_status="paper_ready")
