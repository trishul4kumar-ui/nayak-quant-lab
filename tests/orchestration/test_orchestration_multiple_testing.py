from __future__ import annotations

import pytest

from quantlab.domain.research import CheckResult
from quantlab.orchestration.errors import OrchestrationError
from quantlab.orchestration.multiple_testing import family_correction
from quantlab.research.multiple_testing import CorrectionMethod, evaluate_family


@pytest.mark.orchestration
def test_orchestration_reuses_prompt05_correction() -> None:
    p_values = [0.01, 0.20, 0.40]
    wrapped = family_correction(p_values, method="benjamini_hochberg")
    native = evaluate_family(p_values, method=CorrectionMethod.BENJAMINI_HOCHBERG)
    assert wrapped.adjusted == native.adjusted
    assert wrapped.status is CheckResult.PASS


@pytest.mark.orchestration
def test_omission_is_an_error() -> None:
    with pytest.raises(OrchestrationError, match="omission"):
        family_correction([0.01], omit=True)
