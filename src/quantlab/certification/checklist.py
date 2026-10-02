"""Certification checklist. Missing evidence is NOT_TESTED, never a silent PASS."""

from __future__ import annotations

from quantlab.certification.enums import ChecklistCode, ItemStatus
from quantlab.certification.models import ChecklistItem, Waiver
from quantlab.core.errors import WaiverError

CRITICAL_CODES: frozenset[ChecklistCode] = frozenset(
    {
        ChecklistCode.SAFETY,
        ChecklistCode.DATA_PIT,
        ChecklistCode.PAPER_RECONCILIATION,
        ChecklistCode.AI_GOVERNANCE,
    }
)


def default_items() -> list[ChecklistItem]:
    return [
        ChecklistItem(
            code=code,
            status=ItemStatus.NOT_TESTED,
            critical=code in CRITICAL_CODES,
            note="Missing evidence is NOT_TESTED, not PASS.",
        )
        for code in ChecklistCode
    ]


def apply_waiver(item: ChecklistItem, waiver: Waiver) -> ChecklistItem:
    if not waiver.waiver_id or not waiver.reason or not waiver.authority:
        raise WaiverError("waiver_without_authority: id, reason, and authority are required")
    if not waiver.scope:
        raise WaiverError("waiver_without_authority: scope is required")
    if waiver.expiry <= waiver.timestamp:
        raise WaiverError("waiver_without_authority: expiry must be after timestamp")
    if item.code is ChecklistCode.SAFETY:
        raise WaiverError("SAFETY cannot be waived")
    return item.model_copy(
        update={
            "status": ItemStatus.WAIVED,
            "waiver": waiver,
            "note": f"WAIVED under {waiver.waiver_id}. Not a PASS.",
        }
    )


def merge_status(
    existing: ChecklistItem,
    status: ItemStatus,
    *,
    evidence_id: str,
    note: str,
) -> ChecklistItem:
    if existing.status is ItemStatus.WAIVED:
        return existing
    return existing.model_copy(update={"status": status, "evidence_id": evidence_id, "note": note})
