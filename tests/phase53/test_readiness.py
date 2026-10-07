from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from quantlab.execution_authorization.models import (
    AuthorizationAssessment,
    AuthorizationPolicy,
    AuthorizationScope,
    AuthorizationState,
    HumanApprovalRecord,
)
from quantlab.phase53.models import (
    GatewayDeploymentEvidence,
    GoNoGoState,
    IndependentValidationEvidence,
    Phase53EvidenceBundle,
    Phase53Policy,
    PriorPhaseAcceptanceEvidence,
    RestartRecoveryEvidence,
    ZeroBrokerWriteAuditEvidence,
)
from quantlab.phase53.service import assess_current_state, assess_evidence
from quantlab.production_shadow.models import (
    EvidenceLabel,
    ProductionShadowPolicy,
    ProductionShadowReadiness,
    ProductionShadowRun,
    ShadowCheck,
    ShadowCheckResult,
    ShadowProductionState,
)
from quantlab.realtime_data.hashing import sha256

_NOW = datetime(2026, 10, 8, tzinfo=UTC)


def test_current_state_is_explicitly_incomplete_not_live_enabled() -> None:
    result = assess_current_state(assessed_at=_NOW)

    assert result.state is GoNoGoState.EVIDENCE_INCOMPLETE
    assert result.live_trading is False
    assert result.broker_write_enabled is False
    assert result.execution_gateway_armed is False


def test_complete_dossier_only_reaches_independent_review() -> None:
    runs = (_run("one", _NOW - timedelta(days=2)), _run("two", _NOW))
    scope = _scope()
    assessment = AuthorizationAssessment(
        assessment_id="assessment-1",
        scope=scope,
        policy=AuthorizationPolicy(),
        checks=(),
        blockers=(),
        evidence_hashes=(),
        state=AuthorizationState.ELIGIBLE_FOR_HUMAN_REVIEW,
        assessed_at=_NOW,
        assessment_hash="assessment-hash",
    )
    approval = HumanApprovalRecord(
        approval_id="approval-1",
        assessment_id=assessment.assessment_id,
        assessment_hash=assessment.assessment_hash,
        scope_hash=sha256(scope.model_dump(mode="json")),
        approver_id="human-reviewer",
        approved_at=_NOW,
        expires_at=_NOW + timedelta(minutes=5),
        confirmation="APPROVE assessment-hash",
        approval_hash="approval-hash",
    )
    evidence = Phase53EvidenceBundle(
        prior_phase_acceptance=PriorPhaseAcceptanceEvidence(
            accepted_phases=(49, 50, 51, 52),
            release_references=("ci-49-52",),
            observed_at=_NOW,
            evidence_hash="prior-hash",
        ),
        zero_broker_write_audit=ZeroBrokerWriteAuditEvidence(
            audit_source="independent-read-only-export",
            audited_by="reviewer",
            window_start=_NOW - timedelta(days=3),
            window_end=_NOW + timedelta(days=1),
            broker_write_count=0,
            evidence_hash="zero-write-hash",
        ),
        restart_recovery=RestartRecoveryEvidence(
            scenario_id="restart-1",
            verified_by="reviewer",
            observed_at=_NOW,
            recovered_without_duplicate_submission=True,
            evidence_hash="restart-hash",
        ),
        independent_validation=IndependentValidationEvidence(
            report_id="validation-1",
            reviewer_id="independent-reviewer",
            observed_at=_NOW,
            passed=True,
            evidence_hash="validation-hash",
        ),
        gateway_deployment=GatewayDeploymentEvidence(
            deployment_id="gateway-deployment-1",
            certification_id="gateway-cert-1",
            certified_by="independent-reviewer",
            observed_at=_NOW,
            certified=True,
            evidence_hash="gateway-hash",
        ),
    )

    result = assess_evidence(
        evidence,
        shadow_runs=runs,
        authorization=assessment,
        human_approval=approval,
        policy=Phase53Policy(
            minimum_distinct_observed_sessions=2,
            minimum_observation_window_seconds=60.0,
        ),
        assessed_at=_NOW,
    )

    assert result.state is GoNoGoState.READY_FOR_INDEPENDENT_REVIEW
    assert result.live_trading is False
    assert result.broker_write_enabled is False
    assert result.execution_gateway_armed is False


def test_phase53_has_no_gateway_or_order_write_imports() -> None:
    source = "\n".join(item.read_text() for item in Path("src/quantlab/phase53").glob("*.py"))
    for forbidden in ("kite_execution_gateway", "restricted_execution", "place_order", "submit("):
        assert forbidden not in source


def _run(identifier: str, observed_at: datetime) -> ProductionShadowRun:
    return ProductionShadowRun(
        shadow_run_id=f"shadow-{identifier}",
        policy=ProductionShadowPolicy(),
        checks=(
            ShadowCheck(
                check_id="deterministic_replay",
                result=ShadowCheckResult.PASS,
                critical=True,
                reason="fixture",
            ),
            ShadowCheck(
                check_id="reconciliation",
                result=ShadowCheckResult.PASS,
                critical=True,
                reason="fixture",
            ),
        ),
        readiness=ProductionShadowReadiness(),
        observed_at=observed_at,
        state=ShadowProductionState.RUNNING,
        evidence_labels={"market": EvidenceLabel.OBSERVED, "broker": EvidenceLabel.OBSERVED},
        run_hash=f"run-{identifier}",
    )


def _scope() -> AuthorizationScope:
    return AuthorizationScope(
        deployment_id="deployment-1",
        broker_account_fingerprint="account-fingerprint",
        allowed_security_ids=("NSE:INFY",),
        universe_version="universe-1",
        strategy_hash="strategy",
        model_hash="model",
        portfolio_policy_hash="portfolio",
        release_id="release-1",
        data_provider="recorded-provider",
        data_policy_hash="data",
        risk_policy_hash="risk",
        max_gross_exposure=1.0,
        max_notional=1_000.0,
        max_turnover=0.1,
        operating_mode="human_review",
        session_start=_NOW - timedelta(minutes=1),
        session_end=_NOW + timedelta(minutes=5),
        expiry=_NOW + timedelta(minutes=10),
    )
