"""Live-certification state. CERTIFIED ≠ LIVE_ENABLED ≠ BROKER_CONNECTED."""

from __future__ import annotations

from enum import StrEnum
from threading import Lock

from quantlab.release.errors import InvalidReleaseTransition


class CertState(StrEnum):
    DRAFT = "draft"
    EVIDENCE_COLLECTING = "evidence_collecting"
    VALIDATION_PENDING = "validation_pending"
    VALIDATION_COMPLETE = "validation_complete"
    SHADOW_VERIFIED = "shadow_verified"
    SAFETY_VERIFIED = "safety_verified"
    OPS_VERIFIED = "ops_verified"
    CERTIFICATION_REVIEW = "certification_review"
    CERTIFIED = "certified"
    RELEASE_ELIGIBLE = "release_eligible"
    EXPIRED = "expired"
    SUSPENDED = "suspended"
    REVOKED = "revoked"
    FAILED = "failed"


LEGAL: frozenset[tuple[CertState, CertState]] = frozenset(
    {
        (CertState.DRAFT, CertState.EVIDENCE_COLLECTING),
        (CertState.EVIDENCE_COLLECTING, CertState.VALIDATION_PENDING),
        (CertState.EVIDENCE_COLLECTING, CertState.FAILED),
        (CertState.VALIDATION_PENDING, CertState.VALIDATION_COMPLETE),
        (CertState.VALIDATION_PENDING, CertState.FAILED),
        (CertState.VALIDATION_COMPLETE, CertState.SHADOW_VERIFIED),
        (CertState.VALIDATION_COMPLETE, CertState.FAILED),
        (CertState.SHADOW_VERIFIED, CertState.SAFETY_VERIFIED),
        (CertState.SHADOW_VERIFIED, CertState.FAILED),
        (CertState.SAFETY_VERIFIED, CertState.OPS_VERIFIED),
        (CertState.SAFETY_VERIFIED, CertState.FAILED),
        (CertState.OPS_VERIFIED, CertState.CERTIFICATION_REVIEW),
        (CertState.OPS_VERIFIED, CertState.FAILED),
        (CertState.CERTIFICATION_REVIEW, CertState.CERTIFIED),
        (CertState.CERTIFICATION_REVIEW, CertState.FAILED),
        (CertState.CERTIFIED, CertState.RELEASE_ELIGIBLE),
        (CertState.CERTIFIED, CertState.EXPIRED),
        (CertState.CERTIFIED, CertState.SUSPENDED),
        (CertState.CERTIFIED, CertState.REVOKED),
        (CertState.RELEASE_ELIGIBLE, CertState.EXPIRED),
        (CertState.RELEASE_ELIGIBLE, CertState.SUSPENDED),
        (CertState.RELEASE_ELIGIBLE, CertState.REVOKED),
        (CertState.SUSPENDED, CertState.CERTIFICATION_REVIEW),
        (CertState.SUSPENDED, CertState.REVOKED),
        (CertState.SUSPENDED, CertState.EXPIRED),
    }
)

_LOCK = Lock()
_STATE = CertState.DRAFT


def current() -> CertState:
    return _STATE


def reset_for_tests() -> None:
    global _STATE
    with _LOCK:
        _STATE = CertState.DRAFT


def force(value: CertState) -> CertState:
    global _STATE
    with _LOCK:
        _STATE = value
        return _STATE


def transition(target: CertState) -> CertState:
    global _STATE
    with _LOCK:
        if (_STATE, target) not in LEGAL:
            raise InvalidReleaseTransition(f"{_STATE.value} → {target.value} is illegal")
        _STATE = target
        return _STATE
