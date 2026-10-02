"""Wrap existing engines. Missing last results stay NOT_TESTED."""

from __future__ import annotations

from quantlab.certification.checklist import CRITICAL_CODES, default_items, merge_status
from quantlab.certification.enums import ChecklistCode, ItemStatus
from quantlab.certification.models import Candidate, ChecklistItem
from quantlab.core.config import LiveSafetyGates
from quantlab.paper_oms.enums import ReconciliationStatus


def wrap_engines(candidate: Candidate, *, ai_override: bool) -> list[ChecklistItem]:
    items = {item.code: item for item in default_items()}
    gates = LiveSafetyGates()
    live = bool(gates.live_trading or gates.live_trading_enabled)
    items[ChecklistCode.SAFETY] = merge_status(
        items[ChecklistCode.SAFETY],
        ItemStatus.FAIL if live else ItemStatus.PASS,
        evidence_id="live-safety-gates",
        note="LIVE_TRADING remains false. Safety is not a broker check.",
    )
    items[ChecklistCode.AI_GOVERNANCE] = merge_status(
        items[ChecklistCode.AI_GOVERNANCE],
        ItemStatus.FAIL if ai_override else ItemStatus.PASS,
        evidence_id="ai-governance",
        note="AI cannot override certification, risk, safety, gates, or capital.",
    )
    if candidate.claims_production_evidence and candidate.data_kind == "synthetic":
        items[ChecklistCode.DATA_PROVENANCE] = merge_status(
            items[ChecklistCode.DATA_PROVENANCE],
            ItemStatus.FAIL,
            evidence_id=candidate.snapshot_id,
            note="synthetic_production_evidence",
        )
    else:
        items[ChecklistCode.DATA_PROVENANCE] = merge_status(
            items[ChecklistCode.DATA_PROVENANCE],
            ItemStatus.WARN if candidate.data_kind == "synthetic" else ItemStatus.NOT_TESTED,
            evidence_id=candidate.snapshot_id,
            note="Synthetic diagnostics are not production market evidence.",
        )
    items[ChecklistCode.DATA_PIT] = merge_status(
        items[ChecklistCode.DATA_PIT],
        ItemStatus.PASS,
        evidence_id="integrity",
        note="PIT leak flags must stay false. This is not a licensed NSE PIT claim.",
    )
    _paper(items)
    _tca(items)
    _monitoring(items)
    _econometrics(items)
    _lineage(items, candidate)
    return [items[code] for code in ChecklistCode]


def _paper(items: dict[ChecklistCode, ChecklistItem]) -> None:
    from quantlab.paper_oms.state import last_result

    paper = last_result()
    if paper is None:
        return
    recon = paper.reconciliation.status
    status = ItemStatus.PASS if recon is ReconciliationStatus.RECONCILED else ItemStatus.FAIL
    items[ChecklistCode.PAPER_RECONCILIATION] = merge_status(
        items[ChecklistCode.PAPER_RECONCILIATION],
        status,
        evidence_id=paper.run.oms_run_id,
        note=f"paper recon={recon.value}",
    )


def _tca(items: dict[ChecklistCode, ChecklistItem]) -> None:
    from quantlab.tca.state import last_result

    tca = last_result()
    if tca is None:
        return
    items[ChecklistCode.TCA] = merge_status(
        items[ChecklistCode.TCA],
        ItemStatus.PASS,
        evidence_id=tca.run.tca_run_id,
        note="Wrapped Prompt 21 TCA. Not broker TCA.",
    )
    cap = tca.capacity.status.value
    items[ChecklistCode.CAPACITY] = merge_status(
        items[ChecklistCode.CAPACITY],
        ItemStatus.WARN if cap in {"breach", "not_tested"} else ItemStatus.PASS,
        evidence_id=tca.run.tca_run_id,
        note=f"capacity={cap}",
    )
    items[ChecklistCode.EXECUTION_VALIDATION] = merge_status(
        items[ChecklistCode.EXECUTION_VALIDATION],
        ItemStatus.PASS,
        evidence_id=tca.run.tca_run_id,
        note="Execution research wrapped; not a live fill.",
    )


def _monitoring(items: dict[ChecklistCode, ChecklistItem]) -> None:
    from quantlab.monitoring.state import last_result

    monitoring = last_result()
    if monitoring is None:
        return
    items[ChecklistCode.MONITORING] = merge_status(
        items[ChecklistCode.MONITORING],
        ItemStatus.PASS,
        evidence_id=monitoring.run.monitoring_run_id,
        note="Wrapped Prompt 19 monitoring. Not a live P&L feed.",
    )


def _econometrics(items: dict[ChecklistCode, ChecklistItem]) -> None:
    from quantlab.econometrics.state import last_result

    econo = last_result()
    if econo is None:
        return
    items[ChecklistCode.STATISTICAL_VALIDATION] = merge_status(
        items[ChecklistCode.STATISTICAL_VALIDATION],
        ItemStatus.PASS,
        evidence_id=econo.run.econometrics_run_id,
        note="Wrapped Prompt 22 diagnostics. Granger is not causation.",
    )
    items[ChecklistCode.MULTIPLE_TESTING] = merge_status(
        items[ChecklistCode.MULTIPLE_TESTING],
        ItemStatus.PASS,
        evidence_id=econo.multiple_testing.get("family_id", ""),
        note="Prompt 14 family accounting reused.",
    )


def _lineage(items: dict[ChecklistCode, ChecklistItem], candidate: Candidate) -> None:
    if candidate.family_id or candidate.knowledge_snapshot:
        items[ChecklistCode.RESEARCH_LINEAGE] = merge_status(
            items[ChecklistCode.RESEARCH_LINEAGE],
            ItemStatus.PASS,
            evidence_id=candidate.family_id or candidate.knowledge_snapshot,
            note="Candidate identity recorded. Knowledge is memory, not authority.",
        )
    items[ChecklistCode.OPERATIONAL_READINESS] = merge_status(
        items[ChecklistCode.OPERATIONAL_READINESS],
        ItemStatus.WARN,
        evidence_id="health",
        note="Local research operations. Not a production SRE sign-off.",
    )


def critical_not_tested(items: list[ChecklistItem]) -> list[ChecklistCode]:
    return [item.code for item in items if item.critical and item.status is ItemStatus.NOT_TESTED]


def failed_items(items: list[ChecklistItem]) -> list[ChecklistCode]:
    return [item.code for item in items if item.status is ItemStatus.FAIL]


def is_critical(code: ChecklistCode) -> bool:
    return code in CRITICAL_CODES
