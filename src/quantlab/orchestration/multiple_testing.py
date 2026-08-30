"""Family-level multiple testing. Reuses Prompt 05; does not invent a second FDR engine."""

from __future__ import annotations

from quantlab.domain.research import CheckResult
from quantlab.orchestration.errors import OrchestrationError
from quantlab.research.multiple_testing import (
    CorrectionMethod,
    MultipleTestingReport,
    evaluate_family,
)


def family_correction(
    p_values: list[float],
    *,
    method: str = "benjamini_hochberg",
    alpha: float = 0.05,
    omit: bool = False,
) -> MultipleTestingReport:
    if omit:
        raise OrchestrationError("multiple-testing omission is prohibited for a searched family")
    mapping = {
        "benjamini_hochberg": CorrectionMethod.BENJAMINI_HOCHBERG,
        "bh": CorrectionMethod.BENJAMINI_HOCHBERG,
        "bonferroni": CorrectionMethod.BONFERRONI,
        "holm": CorrectionMethod.HOLM,
    }
    chosen = mapping.get(method, CorrectionMethod.BENJAMINI_HOCHBERG)
    if not p_values:
        return MultipleTestingReport(
            n_hypotheses=0,
            method=chosen,
            alpha=alpha,
            status=CheckResult.NOT_TESTED,
            note="no p-values supplied; family correction not tested",
        )
    return evaluate_family(p_values, method=chosen, alpha=alpha)
