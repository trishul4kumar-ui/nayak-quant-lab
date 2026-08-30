"""Model-risk certification service. Wraps existing engines. Never live."""

from __future__ import annotations

from quantlab import __version__
from quantlab.certification.change import classify_change
from quantlab.certification.checklist import apply_waiver, default_items
from quantlab.certification.enums import (
    CertificationState,
    ChangeClass,
    ItemStatus,
    ReviewerRole,
    SuspensionReason,
)
from quantlab.certification.evidence import wrap_engines
from quantlab.certification.identity import (
    hash_candidate,
    hash_checklist,
    hash_run,
    hash_validation,
    idempotency_key,
)
from quantlab.certification.integrity import CertificationLeakFlags
from quantlab.certification.machine import assert_transition
from quantlab.certification.models import (
    Candidate,
    CertificationRequest,
    CertificationResult,
    CertificationRun,
    ChecklistItem,
)
from quantlab.certification.policy import block_reasons
from quantlab.certification.reproduction import reproduce
from quantlab.certification.risk import assess
from quantlab.certification.state import get_result, last_result, list_runs, put_result
from quantlab.core.config import LiveSafetyGates
from quantlab.core.errors import (
    CertificationError,
    IllegalCertificationTransition,
    SafetyError,
)
from quantlab.domain.research import IntegrityReport
from quantlab.research.integrity import evaluate_integrity


def _integrity(
    flags: CertificationLeakFlags,
    *,
    live_trading: bool,
    data_kind: str,
) -> IntegrityReport:
    return evaluate_integrity(
        bars=[],
        states=[],
        as_of_times=[],
        next_bar_fill=True,
        cost_bps=10.0,
        slippage_model="configured",
        live_trading=live_trading,
        n_experiments_in_family=1,
        used_ml=False,
        data_kind=data_kind,
        illegal_certification_transition=flags.illegal_certification_transition,
        synthetic_production_evidence=flags.synthetic_production_evidence,
        reproduction_break=flags.reproduction_break,
        waiver_without_authority=flags.waiver_without_authority,
        ai_certification_override=flags.ai_certification_override,
        critical_not_tested_certified=flags.critical_not_tested_certified,
    )


def _require(candidate_id: str) -> CertificationResult:
    found = last_result() if candidate_id in {"", "last"} else get_result(candidate_id)
    if found is None:
        raise CertificationError(f"unknown candidate: {candidate_id}")
    return found


def _store(result: CertificationResult) -> CertificationResult:
    key = idempotency_key(
        candidate_id=result.candidate.candidate_id,
        software_version=result.candidate.software_version,
        snapshot_id=result.candidate.snapshot_id,
    )
    return put_result(result, key=key)


def _build_result(
    candidate: Candidate,
    state: CertificationState,
    role: ReviewerRole,
    items: list[ChecklistItem],
    *,
    blocked: bool,
    reasons: list[str],
    request: CertificationRequest,
) -> CertificationResult:
    run = CertificationRun(
        certification_id=f"CERT-{hash_candidate(candidate)[:12]}",
        candidate_id=candidate.candidate_id,
        state=state,
        role=role,
        as_of=request.as_of,
        checklist_hash=hash_checklist(items),
        evidence_hash=hash_validation(candidate, items),
        snapshot_hash=candidate.snapshot_id,
        spec_hash=hash_candidate(candidate),
        validation_hash="",
        live_trading=False,
    )
    run = run.model_copy(update={"validation_hash": hash_run(run)})
    waivers = [item.waiver for item in items if item.waiver is not None]
    return CertificationResult(
        run=run,
        candidate=candidate,
        state=state,
        checklist=items,
        risks=assess(candidate, items),
        waivers=waivers,
        blocked=blocked,
        block_reasons=reasons,
        live_trading=False,
        note=(
            "RESEARCH RESULT ≠ VALIDATED MODEL ≠ APPROVED STRATEGY "
            "≠ DEPLOYABLE STRATEGY ≠ LIVE ORDER AUTHORITY."
        ),
    )


def create_candidate(request: CertificationRequest | None = None) -> CertificationResult:
    used = request or CertificationRequest()
    if used.live_trading or LiveSafetyGates().live_trading:
        raise SafetyError("LIVE_TRADING must remain false; certification is not live permission")
    if used.ai_override:
        _integrity(
            CertificationLeakFlags(ai_certification_override=True),
            live_trading=False,
            data_kind=used.data_kind,
        )
        raise CertificationError("ai_certification_override")
    _ = used.future_payload_ignored
    existing = get_result(used.candidate_id)
    if existing is not None:
        return existing
    candidate = Candidate(
        candidate_id=used.candidate_id,
        snapshot_id="synthetic-diagnostic",
        software_version=__version__,
        data_kind=used.data_kind,
        claims_production_evidence=used.claims_production_evidence,
        family_id="cert-family",
        feature_versions={"seed": "diagnostic"},
    )
    flags = CertificationLeakFlags(
        illegal_certification_transition=False,
        synthetic_production_evidence=used.claims_production_evidence,
        ai_certification_override=False,
        critical_not_tested_certified=False,
        reproduction_break=False,
        waiver_without_authority=False,
    )
    _integrity(flags, live_trading=False, data_kind=used.data_kind)
    items = used.checklist if used.checklist is not None else default_items()
    if used.waiver is not None:
        items = [
            apply_waiver(item, used.waiver) if item.status is ItemStatus.FAIL else item
            for item in items
        ]
    result = _build_result(
        candidate,
        CertificationState.DRAFT,
        used.role,
        items,
        blocked=False,
        reasons=[],
        request=used,
    )
    return _store(result)


def run_validation(
    candidate_id: str = "last",
    request: CertificationRequest | None = None,
) -> CertificationResult:
    used = request or CertificationRequest(candidate_id=candidate_id)
    current = get_result(candidate_id)
    if current is None:
        current = create_candidate(used)
    if used.ai_override:
        raise CertificationError("ai_certification_override")
    if current.state is CertificationState.DRAFT:
        assert_transition(current.state, CertificationState.UNDER_VALIDATION)
        current = _build_result(
            current.candidate,
            CertificationState.UNDER_VALIDATION,
            ReviewerRole.VALIDATOR,
            current.checklist,
            blocked=False,
            reasons=[],
            request=used,
        )
        current = _store(current)
    if current.state is not CertificationState.UNDER_VALIDATION:
        raise IllegalCertificationTransition(
            f"run requires UNDER_VALIDATION, found {current.state.value}"
        )
    items = used.checklist if used.checklist is not None else wrap_engines(
        current.candidate,
        ai_override=used.ai_override,
    )
    if used.waiver is not None:
        items = [
            apply_waiver(item, used.waiver) if item.status is ItemStatus.FAIL else item
            for item in items
        ]
    reasons = block_reasons(current.candidate, items)
    failed = any(reason.startswith("FAIL:") for reason in reasons)
    target = (
        CertificationState.VALIDATION_FAILED
        if failed
        else CertificationState.VALIDATION_PASSED
    )
    assert_transition(current.state, target)
    result = _build_result(
        current.candidate,
        target,
        ReviewerRole.VALIDATOR,
        items,
        blocked=failed,
        reasons=reasons,
        request=used,
    )
    return _store(result)


def transition(
    candidate_id: str,
    target: CertificationState,
    *,
    role: ReviewerRole = ReviewerRole.VALIDATOR,
    request: CertificationRequest | None = None,
) -> CertificationResult:
    used = request or CertificationRequest(candidate_id=candidate_id, role=role)
    if used.ai_override:
        raise CertificationError("ai_certification_override")
    current = _require(candidate_id)
    if target in {
        CertificationState.VALIDATION_PASSED,
        CertificationState.VALIDATION_FAILED,
    }:
        raise IllegalCertificationTransition(
            "illegal certification transition: use run_validation to record the outcome"
        )
    try:
        assert_transition(current.state, target)
        flags = CertificationLeakFlags(illegal_certification_transition=False)
    except IllegalCertificationTransition:
        _integrity(
            CertificationLeakFlags(illegal_certification_transition=True),
            live_trading=False,
            data_kind=current.candidate.data_kind,
        )
        raise
    _integrity(flags, live_trading=False, data_kind=current.candidate.data_kind)
    if target is CertificationState.CERTIFIED:
        return certify(candidate_id, request=used)
    result = _build_result(
        current.candidate,
        target,
        role,
        current.checklist,
        blocked=current.blocked,
        reasons=current.block_reasons,
        request=used,
    )
    return _store(result)


def certify(
    candidate_id: str = "last",
    request: CertificationRequest | None = None,
) -> CertificationResult:
    used = request or CertificationRequest(
        candidate_id=candidate_id,
        role=ReviewerRole.CERTIFICATION_REVIEWER,
    )
    if used.live_trading or LiveSafetyGates().live_trading:
        raise SafetyError("LIVE_TRADING must remain false; CERTIFIED is not live")
    if used.ai_override:
        _integrity(
            CertificationLeakFlags(ai_certification_override=True),
            live_trading=False,
            data_kind=used.data_kind,
        )
        raise CertificationError("ai_certification_override")
    current = _require(candidate_id)
    if used.role is not ReviewerRole.CERTIFICATION_REVIEWER:
        raise CertificationError("certify requires CERTIFICATION_REVIEWER")
    try:
        assert_transition(current.state, CertificationState.CERTIFIED)
    except IllegalCertificationTransition:
        _integrity(
            CertificationLeakFlags(illegal_certification_transition=True),
            live_trading=False,
            data_kind=current.candidate.data_kind,
        )
        raise
    reasons = block_reasons(current.candidate, current.checklist)
    if any(item.startswith("critical_not_tested:") for item in reasons):
        _integrity(
            CertificationLeakFlags(critical_not_tested_certified=True),
            live_trading=False,
            data_kind=current.candidate.data_kind,
        )
        raise CertificationError("critical_not_tested_certified")
    if "synthetic_production_evidence" in reasons:
        _integrity(
            CertificationLeakFlags(synthetic_production_evidence=True),
            live_trading=False,
            data_kind=current.candidate.data_kind,
        )
        raise CertificationError("synthetic_production_evidence")
    if reasons:
        raise CertificationError("certification blocked: " + ",".join(reasons))
    result = _build_result(
        current.candidate,
        CertificationState.CERTIFIED,
        ReviewerRole.CERTIFICATION_REVIEWER,
        current.checklist,
        blocked=False,
        reasons=[],
        request=used,
    )
    return _store(result)


def suspend(
    candidate_id: str,
    reason: SuspensionReason,
    *,
    request: CertificationRequest | None = None,
) -> CertificationResult:
    used = request or CertificationRequest(candidate_id=candidate_id)
    current = _require(candidate_id)
    assert_transition(current.state, CertificationState.SUSPENDED)
    result = _build_result(
        current.candidate,
        CertificationState.SUSPENDED,
        used.role,
        current.checklist,
        blocked=True,
        reasons=[f"suspended:{reason.value}"],
        request=used,
    )
    return _store(result)


def retire(candidate_id: str, request: CertificationRequest | None = None) -> CertificationResult:
    used = request or CertificationRequest(candidate_id=candidate_id)
    current = _require(candidate_id)
    assert_transition(current.state, CertificationState.RETIRED)
    result = _build_result(
        current.candidate,
        CertificationState.RETIRED,
        ReviewerRole.CERTIFICATION_REVIEWER,
        current.checklist,
        blocked=True,
        reasons=["retired"],
        request=used,
    )
    return _store(result)


def reproduce_candidate(candidate_id: str = "last") -> CertificationResult:
    current = _require(candidate_id)
    replay = reproduce(
        current.candidate,
        current.checklist,
        expected_hash=current.run.evidence_hash,
    )
    return current.model_copy(update={"reproduction": replay})


def revise_candidate(after: Candidate) -> ChangeClass:
    current = _require(after.candidate_id)
    klass = classify_change(current.candidate, after)
    if klass is not ChangeClass.MINOR:
        raise CertificationError(
            f"{klass.value} change requires a new candidate version and revalidation"
        )
    return klass


def run_certification(request: CertificationRequest | None = None) -> CertificationResult:
    used = request or CertificationRequest()
    created = create_candidate(used)
    if created.state is CertificationState.DRAFT:
        return run_validation(created.candidate.candidate_id, request=used)
    return created


def diff_candidates(left_id: str, right_id: str) -> dict[str, str]:
    left = _require(left_id)
    right = _require(right_id)
    klass = classify_change(left.candidate, right.candidate)
    return {
        "left": left.candidate.candidate_id,
        "right": right.candidate.candidate_id,
        "change_class": klass.value,
        "left_state": left.state.value,
        "right_state": right.state.value,
        "live_trading": "false",
    }


def all_results() -> list[CertificationResult]:
    return list_runs()
