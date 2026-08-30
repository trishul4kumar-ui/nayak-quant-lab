"""Conservative certification policy. FAIL and critical NOT_TESTED block CERTIFIED."""

from __future__ import annotations

from quantlab.certification.enums import ChecklistCode, ItemStatus
from quantlab.certification.evidence import critical_not_tested, failed_items
from quantlab.certification.models import Candidate, ChecklistItem


def block_reasons(candidate: Candidate, items: list[ChecklistItem]) -> list[str]:
    reasons: list[str] = []
    for code in failed_items(items):
        reasons.append(f"FAIL:{code.value}")
    for code in critical_not_tested(items):
        reasons.append(f"critical_not_tested:{code.value}")
    if candidate.claims_production_evidence and candidate.data_kind == "synthetic":
        reasons.append("synthetic_production_evidence")
    recon = next(
        (item for item in items if item.code is ChecklistCode.PAPER_RECONCILIATION),
        None,
    )
    if recon is not None and recon.status is ItemStatus.FAIL:
        reasons.append("unresolved_reconciliation")
    safety = next((item for item in items if item.code is ChecklistCode.SAFETY), None)
    if safety is not None and safety.status is ItemStatus.FAIL:
        reasons.append("safety_failure")
    return list(dict.fromkeys(reasons))
