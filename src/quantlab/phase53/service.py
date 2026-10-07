"""Fail-closed Phase 53 evidence assessment. No execution adapter is imported."""

from __future__ import annotations

from datetime import UTC, datetime

from quantlab.core.config import LiveSafetyGates
from quantlab.execution_authorization.models import (
    AuthorizationAssessment,
    AuthorizationState,
    HumanApprovalRecord,
)
from quantlab.execution_authorization.repository import (
    approval_for_assessment,
    last_assessment,
    revoked,
)
from quantlab.phase53.models import (
    GateVerdict,
    GoNoGoState,
    Phase53Check,
    Phase53EvidenceBundle,
    Phase53Gate,
    Phase53Policy,
    Phase53Readiness,
)
from quantlab.production_shadow.models import (
    EvidenceLabel,
    ProductionShadowRun,
    ShadowCheckResult,
    ShadowProductionState,
)
from quantlab.production_shadow.repository import history as shadow_history
from quantlab.realtime_data.hashing import sha256


def assess_current_state(
    *, policy: Phase53Policy | None = None, assessed_at: datetime | None = None
) -> Phase53Readiness:
    """Assess recorded read-only evidence only; do not invent missing proof."""
    assessment = last_assessment()
    approval = approval_for_assessment(assessment.assessment_id) if assessment else None
    return assess_evidence(
        Phase53EvidenceBundle(),
        shadow_runs=tuple(shadow_history()),
        authorization=assessment,
        human_approval=approval,
        policy=policy,
        assessed_at=assessed_at,
    )


def assess_evidence(
    evidence: Phase53EvidenceBundle,
    *,
    shadow_runs: tuple[ProductionShadowRun, ...] = (),
    authorization: AuthorizationAssessment | None = None,
    human_approval: HumanApprovalRecord | None = None,
    policy: Phase53Policy | None = None,
    assessed_at: datetime | None = None,
) -> Phase53Readiness:
    """Create an evidence dossier without enabling, configuring, or calling a gateway."""
    used_policy = policy or Phase53Policy()
    now = assessed_at or datetime.now(tz=UTC)
    checks = [
        _prior_phase_check(evidence, used_policy),
        _sustained_shadow_check(shadow_runs, used_policy),
        _zero_write_check(evidence, shadow_runs),
        _replay_check(shadow_runs),
        _reconciliation_check(shadow_runs),
        _restart_recovery_check(evidence),
        _independent_validation_check(evidence),
        _human_authorization_check(authorization, human_approval, now),
        _gateway_deployment_check(evidence),
        _safety_wall_check(),
    ]
    if any(item.verdict is GateVerdict.FAIL for item in checks):
        state = GoNoGoState.BLOCKED
    elif any(item.verdict is GateVerdict.NOT_TESTED for item in checks):
        state = GoNoGoState.EVIDENCE_INCOMPLETE
    else:
        state = GoNoGoState.READY_FOR_INDEPENDENT_REVIEW
    material = {
        "policy": used_policy.model_dump(mode="json"),
        "checks": [item.model_dump(mode="json") for item in checks],
        "assessed_at": now.isoformat(),
    }
    return Phase53Readiness(
        policy=used_policy,
        checks=tuple(checks),
        state=state,
        assessed_at=now,
        dossier_hash=sha256(material),
    )


def _prior_phase_check(
    evidence: Phase53EvidenceBundle, policy: Phase53Policy
) -> Phase53Check:
    item = evidence.prior_phase_acceptance
    if item is None:
        return _not_tested(
            Phase53Gate.PRIOR_PHASE_ACCEPTANCE,
            "prior-phase acceptance evidence missing",
        )
    missing = set(policy.required_prior_phases) - set(item.accepted_phases)
    references = (item.evidence_hash,) if item.evidence_hash else ()
    if missing or not item.release_references or not item.evidence_hash:
        return _fail(
            Phase53Gate.PRIOR_PHASE_ACCEPTANCE,
            f"missing accepted phase references: {sorted(missing)}",
            references,
        )
    return _pass(
        Phase53Gate.PRIOR_PHASE_ACCEPTANCE,
        "all required phase acceptances referenced",
        references,
    )


def _sustained_shadow_check(
    runs: tuple[ProductionShadowRun, ...], policy: Phase53Policy
) -> Phase53Check:
    if not runs:
        return _not_tested(
            Phase53Gate.SUSTAINED_OBSERVED_SHADOW,
            "observed shadow history missing",
        )
    unique_sessions = {item.observed_at.date() for item in runs}
    earliest = min(item.observed_at for item in runs)
    latest = max(item.observed_at for item in runs)
    interval = (latest - earliest).total_seconds()
    observed = all(_observed_non_routable(item) for item in runs)
    references = tuple(item.run_hash for item in runs)
    if not observed:
        return _fail(
            Phase53Gate.SUSTAINED_OBSERVED_SHADOW,
            "shadow history is not wholly observed and non-routable",
            references,
        )
    enough_sessions = len(unique_sessions) >= policy.minimum_distinct_observed_sessions
    enough_window = interval >= policy.minimum_observation_window_seconds
    if not enough_sessions or not enough_window:
        return _not_tested(
            Phase53Gate.SUSTAINED_OBSERVED_SHADOW,
            "sustained observed-session threshold has not been met",
            references,
        )
    return _pass(
        Phase53Gate.SUSTAINED_OBSERVED_SHADOW,
        "sustained observed shadow evidence recorded",
        references,
    )


def _zero_write_check(
    evidence: Phase53EvidenceBundle, runs: tuple[ProductionShadowRun, ...]
) -> Phase53Check:
    item = evidence.zero_broker_write_audit
    if item is None:
        return _not_tested(
            Phase53Gate.ZERO_BROKER_WRITE_AUDIT,
            "independent zero-write audit missing",
        )
    run_times = [run.observed_at for run in runs]
    covers_runs = not run_times or (
        item.window_start <= min(run_times) and item.window_end >= max(run_times)
    )
    references = (item.evidence_hash,) if item.evidence_hash else ()
    complete = item.audit_source and item.audited_by and item.evidence_hash and covers_runs
    if not complete:
        return _fail(
            Phase53Gate.ZERO_BROKER_WRITE_AUDIT,
            "audit evidence is incomplete or does not cover the shadow window",
            references,
        )
    if item.window_end <= item.window_start or item.broker_write_count != 0:
        return _fail(
            Phase53Gate.ZERO_BROKER_WRITE_AUDIT,
            "audit does not prove zero broker writes",
            references,
        )
    return _pass(
        Phase53Gate.ZERO_BROKER_WRITE_AUDIT,
        "independent audit reports zero broker writes",
        references,
    )


def _replay_check(runs: tuple[ProductionShadowRun, ...]) -> Phase53Check:
    if not runs:
        return _not_tested(
            Phase53Gate.DETERMINISTIC_REPLAY,
            "production-shadow history missing",
        )
    references = tuple(item.run_hash for item in runs)
    missing = tuple(
        item.run_hash for item in runs if not _check_passed(item, "deterministic_replay")
    )
    if missing:
        return _fail(
            Phase53Gate.DETERMINISTIC_REPLAY,
            "deterministic replay missing or failed",
            missing,
        )
    return _pass(
        Phase53Gate.DETERMINISTIC_REPLAY,
        "deterministic replay passed for every shadow run",
        references,
    )


def _reconciliation_check(runs: tuple[ProductionShadowRun, ...]) -> Phase53Check:
    if not runs:
        return _not_tested(
            Phase53Gate.RECONCILIATION_CONTINUITY,
            "production-shadow history missing",
        )
    references = tuple(item.run_hash for item in runs)
    missing = tuple(item.run_hash for item in runs if not _check_passed(item, "reconciliation"))
    if missing:
        return _fail(
            Phase53Gate.RECONCILIATION_CONTINUITY,
            "reconciliation missing or failed",
            missing,
        )
    return _pass(
        Phase53Gate.RECONCILIATION_CONTINUITY,
        "reconciliation passed for every shadow run",
        references,
    )


def _restart_recovery_check(evidence: Phase53EvidenceBundle) -> Phase53Check:
    item = evidence.restart_recovery
    if item is None:
        return _not_tested(Phase53Gate.RESTART_RECOVERY, "restart-recovery evidence missing")
    references = (item.evidence_hash,) if item.evidence_hash else ()
    complete = item.scenario_id and item.verified_by and item.evidence_hash
    if not complete or not item.recovered_without_duplicate_submission:
        return _fail(
            Phase53Gate.RESTART_RECOVERY,
            "restart recovery is not independently evidenced",
            references,
        )
    return _pass(
        Phase53Gate.RESTART_RECOVERY,
        "restart recovery recorded without duplicate submission",
        references,
    )


def _independent_validation_check(evidence: Phase53EvidenceBundle) -> Phase53Check:
    item = evidence.independent_validation
    if item is None:
        return _not_tested(
            Phase53Gate.INDEPENDENT_VALIDATION,
            "independent validation evidence missing",
        )
    references = (item.evidence_hash,) if item.evidence_hash else ()
    complete = item.report_id and item.reviewer_id and item.evidence_hash
    if not complete or not item.passed:
        return _fail(
            Phase53Gate.INDEPENDENT_VALIDATION,
            "independent validation did not pass",
            references,
        )
    return _pass(
        Phase53Gate.INDEPENDENT_VALIDATION,
        "independent validation passed",
        references,
    )


def _human_authorization_check(
    assessment: AuthorizationAssessment | None,
    approval: HumanApprovalRecord | None,
    now: datetime,
) -> Phase53Check:
    if assessment is None or approval is None:
        return _not_tested(
            Phase53Gate.HUMAN_AUTHORIZATION,
            "current human authorization evidence missing",
        )
    valid = (
        assessment.state is AuthorizationState.ELIGIBLE_FOR_HUMAN_REVIEW
        and approval.state is AuthorizationState.HUMAN_AUTHORIZED
        and approval.assessment_id == assessment.assessment_id
        and approval.assessment_hash == assessment.assessment_hash
        and approval.scope_hash == sha256(assessment.scope.model_dump(mode="json"))
        and approval.expires_at > now
        and not revoked(approval.approval_id)
        and not assessment.live_trading
        and not assessment.broker_write_enabled
    )
    references = (assessment.assessment_hash, approval.approval_hash)
    if not valid:
        return _fail(
            Phase53Gate.HUMAN_AUTHORIZATION,
            "authorization is expired, revoked, mismatched, or not human-bound",
            references,
        )
    return _pass(
        Phase53Gate.HUMAN_AUTHORIZATION,
        "current human authorization is hash-bound and non-executing",
        references,
    )


def _gateway_deployment_check(evidence: Phase53EvidenceBundle) -> Phase53Check:
    item = evidence.gateway_deployment
    if item is None:
        return _not_tested(
            Phase53Gate.CERTIFIED_GATEWAY_DEPLOYMENT,
            "separately certified gateway deployment evidence missing",
        )
    references = (item.evidence_hash,) if item.evidence_hash else ()
    complete = (
        item.deployment_id
        and item.certification_id
        and item.certified_by
        and item.evidence_hash
    )
    if not complete or not item.certified:
        return _fail(
            Phase53Gate.CERTIFIED_GATEWAY_DEPLOYMENT,
            "gateway deployment is not independently certified",
            references,
        )
    return _pass(
        Phase53Gate.CERTIFIED_GATEWAY_DEPLOYMENT,
        "gateway certification evidence recorded; gateway remains unarmed",
        references,
    )


def _safety_wall_check() -> Phase53Check:
    gates = LiveSafetyGates()
    preserved = (
        not gates.live_trading
        and not gates.broker_write_enabled
        and not gates.execution_gateway_armed
        and gates.shadow_mode
    )
    if not preserved:
        return _fail(
            Phase53Gate.SAFETY_WALL_PRESERVED,
            "Phase 53 assessor requires live and broker writes to remain disabled",
        )
    return _pass(
        Phase53Gate.SAFETY_WALL_PRESERVED,
        "live, broker write, and gateway arming remain disabled",
    )


def _observed_non_routable(item: ProductionShadowRun) -> bool:
    return (
        item.state is ShadowProductionState.RUNNING
        and not item.readiness.critical_failures
        and item.non_routable
        and not item.live_trading
        and not item.broker_write_enabled
        and item.evidence_labels.get("market") is EvidenceLabel.OBSERVED
        and item.evidence_labels.get("broker") is EvidenceLabel.OBSERVED
    )


def _check_passed(run: ProductionShadowRun, check_id: str) -> bool:
    return any(
        item.check_id == check_id and item.result is ShadowCheckResult.PASS
        for item in run.checks
    )


def _pass(
    gate: Phase53Gate, reason: str, references: tuple[str, ...] = ()
) -> Phase53Check:
    return Phase53Check(
        gate=gate,
        verdict=GateVerdict.PASS,
        reason=reason,
        evidence_references=references,
    )


def _fail(
    gate: Phase53Gate, reason: str, references: tuple[str, ...] = ()
) -> Phase53Check:
    return Phase53Check(
        gate=gate,
        verdict=GateVerdict.FAIL,
        reason=reason,
        evidence_references=references,
    )


def _not_tested(
    gate: Phase53Gate, reason: str, references: tuple[str, ...] = ()
) -> Phase53Check:
    return Phase53Check(
        gate=gate,
        verdict=GateVerdict.NOT_TESTED,
        reason=reason,
        evidence_references=references,
    )
