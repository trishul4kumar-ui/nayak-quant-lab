"""Domain criteria. Critical NOT_TESTED and FAIL block certification."""

from __future__ import annotations

from quantlab.core.config import LiveSafetyGates
from quantlab.release.models import (
    CertificationRequest,
    CriterionResult,
    CriterionVerdict,
    ReleaseStage,
)
from quantlab.safety.kill_switch import live_release_blocked
from quantlab.safety.service import last_result as last_safety


def evaluate_criteria(request: CertificationRequest) -> tuple[CriterionResult, ...]:
    gates = LiveSafetyGates()
    safety_ok = (
        not gates.live_trading
        and not request.safety_fail
        and not request.ai_override
        and live_release_blocked()
    )
    safety = last_safety()
    if safety is not None and safety.live_release_authorized:
        safety_ok = False
    rows = [
        CriterionResult(
            criterion_id="research_integrity",
            domain="research",
            verdict=CriterionVerdict.PASS if request.research_ok else CriterionVerdict.NOT_TESTED,
            reason="PIT/lineage evidence" if request.research_ok else "research evidence missing",
        ),
        CriterionResult(
            criterion_id="statistical_validation",
            domain="statistics",
            verdict=(
                CriterionVerdict.PASS if request.statistical_ok else CriterionVerdict.NOT_TESTED
            ),
            reason=(
                "OOS/walk-forward present"
                if request.statistical_ok
                else "single backtest is not enough"
            ),
        ),
        CriterionResult(
            criterion_id="data_readiness",
            domain="data",
            verdict=CriterionVerdict.PASS if request.data_ok else CriterionVerdict.NOT_TESTED,
            reason="production provenance" if request.data_ok else "data readiness not asserted",
        ),
        CriterionResult(
            criterion_id="execution_readiness",
            domain="execution",
            verdict=CriterionVerdict.PASS if request.execution_ok else CriterionVerdict.NOT_TESTED,
            reason=(
                "execution evidence"
                if request.execution_ok
                else "uncalibrated execution remains labelled"
            ),
            critical=False,
        ),
        CriterionResult(
            criterion_id="paper_shadow",
            domain="paper_shadow",
            verdict=(
                CriterionVerdict.PASS if request.paper_shadow_ok else CriterionVerdict.NOT_TESTED
            ),
            reason="paper/shadow lineage" if request.paper_shadow_ok else "paper P&L is not alpha",
        ),
        CriterionResult(
            criterion_id="risk_readiness",
            domain="risk",
            verdict=CriterionVerdict.PASS if request.risk_ok else CriterionVerdict.NOT_TESTED,
            reason="risk snapshot" if request.risk_ok else "unknown risk remains unknown",
        ),
        CriterionResult(
            criterion_id="safety_readiness",
            domain="safety",
            verdict=CriterionVerdict.PASS if safety_ok else CriterionVerdict.FAIL,
            reason="safety fail-closed; G15 BLOCK; live off"
            if safety_ok
            else "safety failure cannot be waived",
        ),
        CriterionResult(
            criterion_id="ops_readiness",
            domain="ops",
            verdict=CriterionVerdict.PASS if request.ops_ok else CriterionVerdict.NOT_TESTED,
            reason="ops doctor evidence" if request.ops_ok else "ops readiness not asserted",
        ),
        CriterionResult(
            criterion_id="independent_validation",
            domain="governance",
            verdict=CriterionVerdict.PASS
            if request.independent_validation and request.validator_id not in {"", request.owner_id}
            else CriterionVerdict.NOT_TESTED,
            reason="independent validator present"
            if request.independent_validation
            else "independent validation missing",
        ),
        CriterionResult(
            criterion_id="reconciliation",
            domain="reconciliation",
            verdict=CriterionVerdict.FAIL if request.recon_break else CriterionVerdict.PASS,
            reason="unresolved recon break" if request.recon_break else "no recon break asserted",
            critical=request.recon_break,
        ),
        CriterionResult(
            criterion_id="synthetic_production",
            domain="governance",
            verdict=CriterionVerdict.FAIL
            if request.synthetic_as_production
            or (
                request.data_kind == "synthetic"
                and request.intended_stage
                in {ReleaseStage.RESTRICTED_LIVE, ReleaseStage.EXPANDED_LIVE}
            )
            else CriterionVerdict.PASS,
            reason="synthetic cannot certify production"
            if request.synthetic_as_production or request.data_kind == "synthetic"
            else "non-synthetic evidence",
        ),
    ]
    if request.intended_stage in {ReleaseStage.RESTRICTED_LIVE, ReleaseStage.EXPANDED_LIVE}:
        # Prompt 27 does not implement unrestricted live; restricted live still blocked.
        rows.append(
            CriterionResult(
                criterion_id="live_enablement",
                domain="governance",
                verdict=CriterionVerdict.FAIL,
                reason="Prompt 27 ends at release eligibility; live remains disabled",
            )
        )
    return tuple(rows)
