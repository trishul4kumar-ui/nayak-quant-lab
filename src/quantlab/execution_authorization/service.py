"""Fail-closed restricted-live eligibility evaluator. No broker write API is imported."""

from __future__ import annotations

from datetime import UTC, datetime

from quantlab.broker_gateway.service import last_snapshot as last_broker_snapshot
from quantlab.core.config import LiveSafetyGates
from quantlab.execution_authorization.models import (
    AuthorizationAssessment,
    AuthorizationCheck,
    AuthorizationEvidence,
    AuthorizationPolicy,
    AuthorizationRevocation,
    AuthorizationScope,
    AuthorizationState,
    CheckVerdict,
    HumanApprovalRecord,
)
from quantlab.execution_authorization.repository import (
    approval as get_approval,
)
from quantlab.execution_authorization.repository import (
    put_approval,
    put_assessment,
    put_revocation,
    revoked,
)
from quantlab.production_shadow.repository import last as last_production_shadow
from quantlab.realtime_data.hashing import sha256
from quantlab.reconciliation.models import ReconciliationStatus
from quantlab.reconciliation.repository import last as last_reconciliation
from quantlab.release.models import CertificationResult
from quantlab.release.service import last_result as last_release
from quantlab.safety.kill_switch import is_active
from quantlab.safety.models import KillScope


def assess(
    scope: AuthorizationScope,
    *,
    evidence: tuple[AuthorizationEvidence, ...] = (),
    policy: AuthorizationPolicy | None = None,
    assessed_at: datetime | None = None,
) -> AuthorizationAssessment:
    """Return eligibility only. This never records human approval or arms execution."""
    used_policy = policy or AuthorizationPolicy()
    now = assessed_at or datetime.now(tz=UTC)
    checks: list[AuthorizationCheck] = []
    _limits(scope, checks)
    _scope_time(scope, now, checks)
    _safety(checks)
    _release(checks)
    _broker(scope, checks)
    _reconciliation(checks)
    _production_shadow(used_policy, checks)
    _evidence(evidence, used_policy, now, checks)
    blockers = tuple(item.check_id for item in checks if item.blocks)
    has_fail = any(item.result is CheckVerdict.FAIL for item in checks)
    state = (
        AuthorizationState.BLOCKED
        if has_fail
        else AuthorizationState.INELIGIBLE
        if blockers
        else AuthorizationState.ELIGIBLE_FOR_HUMAN_REVIEW
    )
    material = {
        "scope": scope.model_dump(mode="json"),
        "policy": used_policy.model_dump(mode="json"),
        "checks": [item.model_dump(mode="json") for item in checks],
        "evidence": sorted(item.content_hash for item in evidence),
        "at": now.isoformat(),
    }
    digest = sha256(material)
    assessment = AuthorizationAssessment(
        assessment_id=f"execution-assessment-{digest[:12]}",
        scope=scope,
        policy=used_policy,
        checks=tuple(checks),
        blockers=blockers,
        evidence_hashes=tuple(sorted(item.content_hash for item in evidence)),
        state=state,
        assessed_at=now,
        assessment_hash=digest,
    )
    return put_assessment(assessment)


def approve(
    assessment: AuthorizationAssessment,
    *,
    approver_id: str,
    confirmation: str,
    approved_at: datetime | None = None,
) -> HumanApprovalRecord:
    """Explicit human review record, hash-bound to a single assessment and scope."""
    now = approved_at or datetime.now(tz=UTC)
    if assessment.state is not AuthorizationState.ELIGIBLE_FOR_HUMAN_REVIEW:
        raise ValueError("only eligible assessments may be approved by a human")
    if not approver_id or approver_id.lower() in {"ai", "llm", "system"}:
        raise ValueError("AI or system actors cannot approve execution eligibility")
    expected = f"APPROVE {assessment.assessment_hash}"
    if confirmation != expected:
        raise ValueError("explicit assessment-hash confirmation is required")
    if assessment.scope.expiry <= now:
        raise ValueError("scope has expired")
    scope_hash = sha256(assessment.scope.model_dump(mode="json"))
    material = {
        "assessment": assessment.assessment_hash,
        "scope": scope_hash,
        "approver": approver_id,
        "at": now.isoformat(),
    }
    digest = sha256(material)
    return put_approval(
        HumanApprovalRecord(
            approval_id=f"human-approval-{digest[:12]}",
            assessment_id=assessment.assessment_id,
            assessment_hash=assessment.assessment_hash,
            scope_hash=scope_hash,
            approver_id=approver_id,
            approved_at=now,
            expires_at=assessment.scope.expiry,
            confirmation=confirmation,
            approval_hash=digest,
        )
    )


def revoke(
    approval_id: str, *, reason: str, revoked_by: str, revoked_at: datetime | None = None
) -> AuthorizationRevocation:
    now = revoked_at or datetime.now(tz=UTC)
    if not reason or not revoked_by:
        raise ValueError("revocation requires reason and attributable human actor")
    if get_approval(approval_id) is None:
        raise KeyError(approval_id)
    digest = sha256(
        {"approval": approval_id, "reason": reason, "by": revoked_by, "at": now.isoformat()}
    )
    return put_revocation(
        AuthorizationRevocation(
            revocation_id=f"revocation-{digest[:12]}",
            approval_id=approval_id,
            reason=reason,
            revoked_by=revoked_by,
            revoked_at=now,
            revocation_hash=digest,
        )
    )


def approval_valid(
    item: HumanApprovalRecord, scope: AuthorizationScope, *, now: datetime | None = None
) -> bool:
    at = now or datetime.now(tz=UTC)
    return (
        item.expires_at > at
        and not revoked(item.approval_id)
        and item.scope_hash == sha256(scope.model_dump(mode="json"))
        and item.live_trading is False
    )


def _limits(scope: AuthorizationScope, checks: list[AuthorizationCheck]) -> None:
    values = (scope.max_gross_exposure, scope.max_notional, scope.max_turnover)
    valid = all(item is not None and item > 0 for item in values)
    checks.append(
        _check(
            "risk_limits",
            CheckVerdict.PASS if valid else CheckVerdict.FAIL,
            "explicit positive risk limits required",
        )
    )


def _scope_time(scope: AuthorizationScope, now: datetime, checks: list[AuthorizationCheck]) -> None:
    valid = scope.session_start < scope.session_end < scope.expiry and now < scope.expiry
    checks.append(
        _check(
            "scope_window",
            CheckVerdict.PASS if valid else CheckVerdict.FAIL,
            "session window and expiry must be explicit and current",
        )
    )


def _safety(checks: list[AuthorizationCheck]) -> None:
    gates = LiveSafetyGates()
    safe = not gates.live_trading and not gates.broker_write_enabled and gates.shadow_mode
    global_kill = is_active(KillScope.GLOBAL)
    checks.append(
        _check(
            "safety_wall",
            CheckVerdict.PASS if safe else CheckVerdict.FAIL,
            "live and broker-write remain disabled",
        )
    )
    checks.append(
        _check(
            "kill_switch",
            CheckVerdict.FAIL if global_kill else CheckVerdict.PASS,
            "global kill switch must be inactive",
        )
    )


def _release(checks: list[AuthorizationCheck]) -> None:
    result: CertificationResult | None = last_release()
    if result is None:
        checks.append(
            _check("release_certification", CheckVerdict.NOT_TESTED, "release evidence missing")
        )
        return
    ready = result.state.value == "release_eligible" and not result.blocked
    checks.append(
        _check(
            "release_certification",
            CheckVerdict.PASS if ready else CheckVerdict.FAIL,
            "release eligibility does not equal execution authorization",
        )
    )


def _broker(scope: AuthorizationScope, checks: list[AuthorizationCheck]) -> None:
    broker = last_broker_snapshot()
    if broker is None:
        checks.append(
            _check("broker_identity", CheckVerdict.NOT_TESTED, "broker observation missing")
        )
        return
    exact = broker.profile.account_id_hash == scope.broker_account_fingerprint
    checks.append(
        _check(
            "broker_identity",
            CheckVerdict.PASS if exact else CheckVerdict.FAIL,
            "broker account fingerprint must match scope",
        )
    )


def _reconciliation(checks: list[AuthorizationCheck]) -> None:
    report = last_reconciliation()
    if report is None:
        checks.append(
            _check("reconciliation", CheckVerdict.NOT_TESTED, "reconciliation evidence missing")
        )
        return
    valid = report.status in {ReconciliationStatus.MATCH, ReconciliationStatus.MATCH_WITH_TOLERANCE}
    checks.append(
        _check(
            "reconciliation", CheckVerdict.PASS if valid else CheckVerdict.FAIL, report.status.value
        )
    )


def _production_shadow(policy: AuthorizationPolicy, checks: list[AuthorizationCheck]) -> None:
    run = last_production_shadow()
    if run is None:
        checks.append(
            _check(
                "production_shadow", CheckVerdict.NOT_TESTED, "production-shadow evidence missing"
            )
        )
        return
    ready = not run.readiness.critical_failures
    checks.append(
        _check(
            "production_shadow", CheckVerdict.PASS if ready else CheckVerdict.FAIL, run.state.value
        )
    )
    if policy.require_shadow_replay:
        replay = next(
            (item for item in run.checks if item.check_id == "deterministic_replay"), None
        )
        passed = replay is not None and replay.result.value == CheckVerdict.PASS.value
        checks.append(
            _check(
                "shadow_replay",
                CheckVerdict.PASS if passed else CheckVerdict.NOT_TESTED,
                "deterministic replay evidence required",
            )
        )


def _evidence(
    evidence: tuple[AuthorizationEvidence, ...],
    policy: AuthorizationPolicy,
    now: datetime,
    checks: list[AuthorizationCheck],
) -> None:
    if not evidence:
        checks.append(
            _check(
                "audit_evidence", CheckVerdict.NOT_TESTED, "hash-verifiable audit evidence missing"
            )
        )
        return
    fresh = all(
        (now - item.observed_at).total_seconds() <= policy.max_evidence_age_seconds
        for item in evidence
    )
    complete = all(bool(item.content_hash and item.source and item.provenance) for item in evidence)
    checks.append(
        _check(
            "audit_evidence",
            CheckVerdict.PASS if fresh and complete else CheckVerdict.FAIL,
            "evidence must be complete and fresh",
        )
    )


def _check(check_id: str, result: CheckVerdict, reason: str) -> AuthorizationCheck:
    return AuthorizationCheck(
        check_id=check_id,
        result=result,
        severity="critical",
        evidence=(sha256({"check": check_id, "result": result.value, "reason": reason}),),
        reason=reason,
    )
