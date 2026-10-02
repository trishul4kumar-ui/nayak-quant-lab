"""Strict certification state machine. Never DRAFT → CERTIFIED. Never live."""

from __future__ import annotations

from quantlab.certification.enums import CertificationState
from quantlab.core.errors import IllegalCertificationTransition

_ALLOWED: dict[CertificationState, frozenset[CertificationState]] = {
    CertificationState.DRAFT: frozenset({CertificationState.UNDER_VALIDATION}),
    CertificationState.UNDER_VALIDATION: frozenset(
        {
            CertificationState.VALIDATION_FAILED,
            CertificationState.VALIDATION_PASSED,
        }
    ),
    CertificationState.VALIDATION_FAILED: frozenset(
        {
            CertificationState.UNDER_VALIDATION,
            CertificationState.SUSPENDED,
            CertificationState.RETIRED,
        }
    ),
    CertificationState.VALIDATION_PASSED: frozenset(
        {
            CertificationState.PAPER_ELIGIBLE,
            CertificationState.UNDER_VALIDATION,
        }
    ),
    CertificationState.PAPER_ELIGIBLE: frozenset(
        {
            CertificationState.PAPER_ACTIVE,
            CertificationState.UNDER_VALIDATION,
            CertificationState.SUSPENDED,
            CertificationState.RETIRED,
        }
    ),
    CertificationState.PAPER_ACTIVE: frozenset(
        {
            CertificationState.PAPER_FAILED,
            CertificationState.SHADOW_ELIGIBLE,
            CertificationState.SUSPENDED,
        }
    ),
    CertificationState.PAPER_FAILED: frozenset(
        {
            CertificationState.PAPER_ELIGIBLE,
            CertificationState.UNDER_VALIDATION,
            CertificationState.SUSPENDED,
            CertificationState.RETIRED,
        }
    ),
    CertificationState.SHADOW_ELIGIBLE: frozenset(
        {
            CertificationState.SHADOW_ACTIVE,
            CertificationState.SUSPENDED,
            CertificationState.RETIRED,
        }
    ),
    CertificationState.SHADOW_ACTIVE: frozenset(
        {
            CertificationState.PRELIVE_REVIEW,
            CertificationState.SUSPENDED,
        }
    ),
    CertificationState.PRELIVE_REVIEW: frozenset(
        {
            CertificationState.CERTIFIED,
            CertificationState.SUSPENDED,
            CertificationState.UNDER_VALIDATION,
        }
    ),
    CertificationState.CERTIFIED: frozenset(
        {
            CertificationState.SUSPENDED,
            CertificationState.RETIRED,
        }
    ),
    CertificationState.SUSPENDED: frozenset(
        {
            CertificationState.UNDER_VALIDATION,
            CertificationState.RETIRED,
        }
    ),
    CertificationState.RETIRED: frozenset(),
}


def allowed_targets(current: CertificationState) -> frozenset[CertificationState]:
    return _ALLOWED[current]


def assert_transition(current: CertificationState, target: CertificationState) -> None:
    if target is current:
        raise IllegalCertificationTransition(f"no-op transition is not recorded: {current.value}")
    if target not in _ALLOWED[current]:
        raise IllegalCertificationTransition(
            f"illegal certification transition: {current.value} → {target.value}"
        )
