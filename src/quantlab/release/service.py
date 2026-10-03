"""Live-trading certification and promotion gate. Not a broker. Not live."""

from __future__ import annotations

from quantlab.core.config import LiveSafetyGates
from quantlab.data.fabric.checksums import sha256_bytes
from quantlab.release.audit import history
from quantlab.release.audit import record as record_audit
from quantlab.release.audit import reset_for_tests as reset_audit
from quantlab.release.errors import CertificationBlocked, InvalidReleaseTransition
from quantlab.release.gates import evaluate_criteria
from quantlab.release.manifest import mint_manifest, mint_package
from quantlab.release.models import (
    ActorKind,
    CertificationRequest,
    CertificationResult,
    CriterionResult,
    WaiverRecord,
)
from quantlab.release.repository import get, last, list_results, put
from quantlab.release.repository import reset_for_tests as reset_repo
from quantlab.release.state import CertState, current, force, transition
from quantlab.release.state import reset_for_tests as reset_state
from quantlab.release.waivers import list_waivers
from quantlab.release.waivers import record as record_waiver
from quantlab.release.waivers import reset_for_tests as reset_waivers

_HAPPY_PATH: tuple[CertState, ...] = (
    CertState.DRAFT,
    CertState.EVIDENCE_COLLECTING,
    CertState.VALIDATION_PENDING,
    CertState.VALIDATION_COMPLETE,
    CertState.SHADOW_VERIFIED,
    CertState.SAFETY_VERIFIED,
    CertState.OPS_VERIFIED,
    CertState.CERTIFICATION_REVIEW,
    CertState.CERTIFIED,
    CertState.RELEASE_ELIGIBLE,
)


def reset_for_tests() -> None:
    reset_state()
    reset_repo()
    reset_audit()
    reset_waivers()


def _hash(result: CertificationResult) -> str:
    material = (
        f"{result.evaluation_id}|{result.state.value}|"
        + "|".join(f"{c.criterion_id}:{c.verdict.value}" for c in result.criteria)
        + f"|{result.live_enabled}|{result.package.package_hash if result.package else ''}"
    )
    return sha256_bytes(material.encode())


def _blocked(request: CertificationRequest, criteria: tuple[CriterionResult, ...]) -> bool:
    if request.ai_override or request.actor is ActorKind.AI_SUGGESTION:
        return True
    if request.expired:
        return True
    if request.model_mutated or request.config_mutated:
        return True
    return any(item.blocks for item in criteria)


def advance_to(target: CertState) -> CertState:
    """Walk the legal happy path. Direct DRAFT→CERTIFIED remains illegal."""
    here = current()
    if here is target:
        return here
    if here not in _HAPPY_PATH or target not in _HAPPY_PATH:
        raise InvalidReleaseTransition(f"{here.value} → {target.value} is illegal")
    start = _HAPPY_PATH.index(here)
    end = _HAPPY_PATH.index(target)
    if end <= start:
        raise InvalidReleaseTransition(f"{here.value} → {target.value} is illegal")
    for nxt in _HAPPY_PATH[start + 1 : end + 1]:
        transition(nxt)
    return current()


def evaluate(request: CertificationRequest | None = None) -> CertificationResult:
    request = request or CertificationRequest()
    gates = LiveSafetyGates()
    criteria = evaluate_criteria(request)
    pkg = mint_package(request)
    result = CertificationResult(
        evaluation_id=f"rel-{request.package_id}",
        state=current(),
        package=pkg,
        criteria=criteria,
        live_trading=gates.live_trading,
        live_enabled=False,
        broker_connected=False,
        blocked=True,
        extras={
            "owner_id": request.owner_id,
            "validator_id": request.validator_id,
            "package_hash": pkg.package_hash,
            "criteria_blocked": _blocked(request, criteria),
            "broker_write_enabled": gates.broker_write_enabled,
        },
    )
    result = result.model_copy(update={"result_hash": _hash(result)})
    put(result)
    record_audit(result)
    return result


def evaluate_release_gate(request: CertificationRequest | None = None) -> CertificationResult:
    return evaluate(request)


def run_certification_package(request: CertificationRequest | None = None) -> CertificationResult:
    return evaluate(request)


def create(request: CertificationRequest | None = None) -> CertificationResult:
    force(CertState.DRAFT)
    evaluate(request)
    transition(CertState.EVIDENCE_COLLECTING)
    return evaluate(request)


def certify(request: CertificationRequest | None = None) -> CertificationResult:
    request = request or CertificationRequest()
    if request.ai_override or request.actor is ActorKind.AI_SUGGESTION:
        raise CertificationBlocked("AI cannot certify")
    if request.expired:
        raise CertificationBlocked("expired certification")
    if request.model_mutated or request.config_mutated:
        raise CertificationBlocked("material mutation invalidates certification")
    result = evaluate(request)
    if any(item.blocks for item in result.criteria):
        raise CertificationBlocked("critical FAIL or NOT_TESTED blocks certification")
    if request.human_role is ActorKind.AI_SUGGESTION:
        raise CertificationBlocked("AI cannot approve")
    if current() is CertState.CERTIFIED:
        updated = evaluate(request)
        return updated.model_copy(update={"state": CertState.CERTIFIED, "blocked": True})
    advance_to(CertState.CERTIFIED)
    updated = evaluate(request)
    return updated.model_copy(update={"state": CertState.CERTIFIED, "blocked": True})


def approve(request: CertificationRequest | None = None) -> CertificationResult:
    request = request or CertificationRequest()
    if request.actor is ActorKind.AI_SUGGESTION or request.ai_override:
        raise CertificationBlocked("AI cannot authorize")
    if request.human_role is not ActorKind.RELEASE_AUTHORITY:
        raise CertificationBlocked("human approval missing")
    if request.human_approver_id in {"", request.owner_id, request.validator_id}:
        raise CertificationBlocked("separation of duties violation")
    result = evaluate(request)
    if any(item.blocks for item in result.criteria):
        raise CertificationBlocked("human approval cannot bypass FAIL or NOT_TESTED")
    if current() is CertState.RELEASE_ELIGIBLE:
        pass
    elif current() is CertState.CERTIFIED:
        transition(CertState.RELEASE_ELIGIBLE)
    else:
        raise InvalidReleaseTransition(f"{current().value} cannot become release eligible")
    manifest = mint_manifest(request, release_id=f"relman-{request.package_id}")
    updated = evaluate(request)
    eligible = updated.model_copy(
        update={
            "state": CertState.RELEASE_ELIGIBLE,
            "manifest": manifest,
            "live_enabled": False,
            "blocked": False,
            "note": (
                "RELEASE_ELIGIBLE permits restricted human-review eligibility only. "
                "LIVE_TRADING and broker writes remain disabled."
            ),
        }
    )
    # Persist the reviewed release state.  ``blocked=False`` is deliberately
    # not a live-trading flag: ``live_enabled`` and ``live_trading`` remain
    # false, while the authorization service can evaluate the release evidence.
    return put(eligible)


def reject(request: CertificationRequest | None = None) -> CertificationResult:
    force(CertState.FAILED)
    return evaluate(request)


def expire() -> CertificationResult:
    if current() in {CertState.CERTIFIED, CertState.RELEASE_ELIGIBLE, CertState.SUSPENDED}:
        transition(CertState.EXPIRED)
    else:
        force(CertState.EXPIRED)
    return evaluate()


def suspend() -> CertificationResult:
    if current() in {CertState.CERTIFIED, CertState.RELEASE_ELIGIBLE}:
        transition(CertState.SUSPENDED)
    else:
        force(CertState.SUSPENDED)
    return evaluate()


def revoke() -> CertificationResult:
    if current() in {
        CertState.CERTIFIED,
        CertState.RELEASE_ELIGIBLE,
        CertState.SUSPENDED,
    }:
        transition(CertState.REVOKED)
    else:
        force(CertState.REVOKED)
    return evaluate()


def add_waiver(item: WaiverRecord) -> WaiverRecord:
    return record_waiver(item)


def last_result() -> CertificationResult | None:
    return last()


def inspect(item_id: str = "last") -> CertificationResult | None:
    return get(item_id)


def list_packages() -> list[CertificationResult]:
    return list_results()


def audit_history() -> list[CertificationResult]:
    return history()


def waivers() -> list[WaiverRecord]:
    return list_waivers()


def default_passing_request() -> CertificationRequest:
    """Research-stage package with independent validation. Still not live."""
    return CertificationRequest(
        package_id="LIVE-CERT-PASS",
        owner_id="researcher-1",
        validator_id="validator-1",
        data_kind="synthetic",
        research_ok=True,
        statistical_ok=True,
        data_ok=True,
        execution_ok=True,
        paper_shadow_ok=True,
        risk_ok=True,
        ops_ok=True,
        independent_validation=True,
        actor=ActorKind.RELEASE_AUTHORITY,
        human_approver_id="authority-1",
        human_role=ActorKind.RELEASE_AUTHORITY,
        max_capital=0.0,
    )
