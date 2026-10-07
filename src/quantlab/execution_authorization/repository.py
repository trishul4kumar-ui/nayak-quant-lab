"""Append-only authorization assessments and human action audit."""

from __future__ import annotations

from threading import Lock

from quantlab.execution_authorization.models import (
    AuthorizationAssessment,
    AuthorizationRevocation,
    HumanApprovalRecord,
)

_LOCK = Lock()
_ASSESSMENTS: dict[str, AuthorizationAssessment] = {}
_APPROVALS: dict[str, HumanApprovalRecord] = {}
_REVOKED: dict[str, AuthorizationRevocation] = {}
_ORDER: list[str] = []
_AUDIT: list[dict[str, str]] = []


def reset_for_tests() -> None:
    with _LOCK:
        _ASSESSMENTS.clear()
        _APPROVALS.clear()
        _REVOKED.clear()
        _ORDER.clear()
        _AUDIT.clear()


def put_assessment(item: AuthorizationAssessment) -> AuthorizationAssessment:
    with _LOCK:
        existing = _ASSESSMENTS.get(item.assessment_id)
        if existing is not None and existing.assessment_hash != item.assessment_hash:
            raise ValueError("authorization assessment identity collision")
        if existing is not None:
            return existing
        _ASSESSMENTS[item.assessment_id] = item
        _ORDER.append(item.assessment_id)
        _AUDIT.append({"event": "assessed", "assessment_id": item.assessment_id})
        return item


def last_assessment() -> AuthorizationAssessment | None:
    with _LOCK:
        return _ASSESSMENTS[_ORDER[-1]] if _ORDER else None


def put_approval(item: HumanApprovalRecord) -> HumanApprovalRecord:
    with _LOCK:
        existing = _APPROVALS.get(item.approval_id)
        if existing is not None and existing.approval_hash != item.approval_hash:
            raise ValueError("authorization approval identity collision")
        _APPROVALS[item.approval_id] = item
        _AUDIT.append({"event": "human_approved", "approval_id": item.approval_id})
        return item


def approval(approval_id: str) -> HumanApprovalRecord | None:
    with _LOCK:
        return _APPROVALS.get(approval_id)


def approval_for_assessment(assessment_id: str) -> HumanApprovalRecord | None:
    """Return the latest approval bound to an assessment without creating authority."""
    with _LOCK:
        return next(
            (
                item
                for item in reversed(tuple(_APPROVALS.values()))
                if item.assessment_id == assessment_id
            ),
            None,
        )


def put_revocation(item: AuthorizationRevocation) -> AuthorizationRevocation:
    with _LOCK:
        if item.approval_id in _REVOKED:
            return _REVOKED[item.approval_id]
        _REVOKED[item.approval_id] = item
        _AUDIT.append({"event": "revoked", "approval_id": item.approval_id})
        return item


def revoked(approval_id: str) -> bool:
    with _LOCK:
        return approval_id in _REVOKED


def audit() -> list[dict[str, str]]:
    with _LOCK:
        return list(_AUDIT)
