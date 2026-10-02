"""Live-certification integrity mapping. Unset flags remain NOT_TESTED."""

from __future__ import annotations

from quantlab.domain.research import IntegrityReport
from quantlab.release.models import ActorKind, CertificationRequest, CertificationResult
from quantlab.research.integrity import evaluate_integrity


def report_from_result(
    result: CertificationResult,
    request: CertificationRequest | None = None,
) -> IntegrityReport:
    request = request or CertificationRequest()
    blocked_ids = {item.criterion_id for item in result.criteria if item.blocks}
    return evaluate_integrity(
        bars=[],
        states=[],
        as_of_times=[],
        next_bar_fill=True,
        cost_bps=10.0,
        slippage_model="none",
        live_trading=result.live_trading,
        n_experiments_in_family=1,
        used_ml=False,
        independent_validation_missing="independent_validation" in blocked_ids,
        safety_gate_failure="safety_readiness" in blocked_ids,
        reconciliation_failure="reconciliation" in blocked_ids,
        revoked_certification=result.state.value == "revoked",
        ai_authorization_override=request.ai_override or request.actor is ActorKind.AI_SUGGESTION,
        capital_limit_mutation=request.max_capital > 0 and request.model_mutated,
        release_policy_mutation=request.config_mutated,
        certification_hash_mismatch=request.model_mutated,
        human_approval_missing=request.human_role is ActorKind.SYSTEM,
    )
