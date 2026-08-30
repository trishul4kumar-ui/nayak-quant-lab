"""Model-risk taxonomy. Severity is explicit; NOT_ASSESSED is the honest default."""

from __future__ import annotations

from quantlab.certification.enums import ItemStatus, RiskCategory, RiskSeverity
from quantlab.certification.models import Candidate, ChecklistItem, ModelRiskAssessment


def assess(candidate: Candidate, items: list[ChecklistItem]) -> list[ModelRiskAssessment]:
    by_code = {item.code.value: item.status for item in items}
    rows: list[ModelRiskAssessment] = []
    for category in RiskCategory:
        severity = RiskSeverity.NOT_ASSESSED
        note = "Not assessed. Absence of a score is not LOW."
        if category is RiskCategory.DATA:
            if candidate.claims_production_evidence and candidate.data_kind == "synthetic":
                severity = RiskSeverity.CRITICAL
                note = "Synthetic diagnostics claimed as production evidence."
            elif candidate.data_kind == "synthetic":
                severity = RiskSeverity.MEDIUM
                note = "Synthetic research diagnostic. Not NSE evidence."
        elif category is RiskCategory.OVERFITTING:
            status = by_code.get("oos_validation", ItemStatus.NOT_TESTED)
            severity = (
                RiskSeverity.HIGH
                if status is ItemStatus.NOT_TESTED
                else RiskSeverity.MEDIUM
            )
            note = "OOS absence keeps overfitting risk visible."
        elif category is RiskCategory.EXECUTION:
            status = by_code.get("tca", ItemStatus.NOT_TESTED)
            severity = (
                RiskSeverity.HIGH
                if status is ItemStatus.NOT_TESTED
                else RiskSeverity.MEDIUM
            )
            note = "Missing TCA is not a free execution assumption."
        elif category is RiskCategory.GOVERNANCE:
            status = by_code.get("ai_governance", ItemStatus.NOT_TESTED)
            severity = RiskSeverity.CRITICAL if status is ItemStatus.FAIL else RiskSeverity.LOW
            note = "AI cannot certify, override gates, or request live orders."
        elif category is RiskCategory.OPERATIONAL:
            status = by_code.get("paper_reconciliation", ItemStatus.NOT_TESTED)
            if status is ItemStatus.FAIL:
                severity = RiskSeverity.CRITICAL
                note = "Unresolved paper reconciliation."
            elif status is ItemStatus.NOT_TESTED:
                severity = RiskSeverity.HIGH
                note = "Paper reconciliation not evidenced."
        rows.append(ModelRiskAssessment(category=category, severity=severity, note=note))
    return rows
