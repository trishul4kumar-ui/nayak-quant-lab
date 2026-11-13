"""Frozen contracts for the institutional research desk and its presentation."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal, Self

from pydantic import AwareDatetime, Field, model_validator

from quantlab.agents.contracts import EvidenceStatus
from quantlab.agents.hashing import Artifact
from quantlab.agents.research import Draft


class InstitutionRole(StrEnum):
    SUPERVISOR = "SUPERVISOR"
    BULL = "BULL"
    BEAR = "BEAR"
    NEWS_DOCS = "NEWS_DOCS"
    QUANT = "QUANT"
    RISK = "RISK"
    EXECUTION_MONITOR = "EXECUTION_MONITOR"
    AUDIT = "AUDIT"


class InstitutionStatus(StrEnum):
    COMPLETE = "COMPLETE"
    ABSTAIN = "ABSTAIN"
    BLOCKED = "BLOCKED"
    CANCELLED = "CANCELLED"


LABELS = {
    InstitutionRole.SUPERVISOR: "Desk Supervisor",
    InstitutionRole.BULL: "Bull Analyst",
    InstitutionRole.BEAR: "Bear Analyst",
    InstitutionRole.NEWS_DOCS: "News / Documents",
    InstitutionRole.QUANT: "Quant Research",
    InstitutionRole.RISK: "Risk Officer",
    InstitutionRole.EXECUTION_MONITOR: "Execution Monitor",
    InstitutionRole.AUDIT: "Audit / Evidence",
}

MANDATES = {
    InstitutionRole.SUPERVISOR: "Consolidate seven frozen reports and unresolved evidence.",
    InstitutionRole.BULL: "Investigate long-side hypotheses and search for contrary evidence.",
    InstitutionRole.BEAR: "Investigate downside, invalidation, liquidity and adverse regimes.",
    InstitutionRole.NEWS_DOCS: "Review documents; separate source claims from verified facts.",
    InstitutionRole.QUANT: "Explain canonical feature, factor, regime and validation tool results.",
    InstitutionRole.RISK: "Explain available deterministic risk evidence and unresolved limits.",
    InstitutionRole.EXECUTION_MONITOR: "Review supplied execution and reconciliation evidence.",
    InstitutionRole.AUDIT: "Review provenance, evidence gaps and the frozen artifact ledger.",
}


class InstitutionDocument(Artifact):
    title: str = Field(min_length=1, max_length=160)
    text: str = Field(min_length=1, max_length=6000)
    available_at: AwareDatetime
    trust: Literal["UNTRUSTED_SOURCE"] = "UNTRUSTED_SOURCE"


class InstitutionEvidence(Artifact):
    run_id: str
    snapshot_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    kind: str = Field(max_length=100)
    status: EvidenceStatus
    available_at: AwareDatetime
    source_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    detail: str = Field(min_length=1, max_length=7000)
    trust: Literal["HOST_RECORD", "UNTRUSTED_SOURCE", "MODEL_OPINION"] = "HOST_RECORD"


class InstitutionClaim(Draft):
    text: str = Field(min_length=1, max_length=500)
    evidence_hashes: tuple[str, ...] = Field(min_length=1, max_length=8)


class InstitutionDraft(Draft):
    """Compact local-model schema; each displayed sentence carries citations."""

    status: Literal["COMPLETE", "ABSTAIN"]
    claims: tuple[InstitutionClaim, ...] = Field(min_length=1, max_length=3)


class InstitutionReport(Artifact):
    run_id: str
    snapshot_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    role: InstitutionRole
    status: InstitutionStatus
    task: str = Field(min_length=1, max_length=500)
    summary: str = Field(min_length=1, max_length=2000)
    claims: tuple[InstitutionClaim, ...] = Field(max_length=4)
    evidence_hashes: tuple[str, ...] = Field(max_length=80)
    source_run_hash: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    source_memo_hash: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    error_code: str | None = Field(default=None, max_length=100)
    authored_by: Literal["MODEL", "HOST_ABSTENTION", "ANALYST_WORKER"]
    validation: Literal["NOT_TESTED"] = "NOT_TESTED"
    execution_authority: Literal[False] = False

    @model_validator(mode="after")
    def citations_are_owned(self) -> Self:
        owned = set(self.evidence_hashes)
        if len(owned) != len(self.evidence_hashes):
            raise ValueError("DUPLICATE_EVIDENCE_REFERENCE")
        if any(not set(claim.evidence_hashes) <= owned for claim in self.claims):
            raise ValueError("FOREIGN_CLAIM_REFERENCE")
        if self.status is InstitutionStatus.COMPLETE and not self.claims:
            raise ValueError("COMPLETED_REPORT_REQUIRES_CITED_CLAIMS")
        return self


class DeskCycle(Artifact):
    run_id: str
    snapshot_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    snapshot_artifact_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    as_of: AwareDatetime
    security_scope: tuple[str, ...]
    reports: tuple[InstitutionReport, ...] = Field(min_length=7, max_length=7)
    supervisor_report: InstitutionReport
    evidence_hashes: tuple[str, ...] = Field(max_length=100)
    status: InstitutionStatus
    summary: str = Field(min_length=1, max_length=2500)
    synthetic: bool
    replay: bool
    execution_authority: Literal[False] = False
    live_trading: Literal[False] = False
    broker_write_enabled: Literal[False] = False

    @model_validator(mode="after")
    def complete_hierarchy(self) -> Self:
        expected = set(InstitutionRole) - {InstitutionRole.SUPERVISOR}
        if {item.role for item in self.reports} != expected:
            raise ValueError("ALL_SEVEN_RESEARCH_ROLES_REQUIRED")
        if self.supervisor_report.role is not InstitutionRole.SUPERVISOR:
            raise ValueError("SUPERVISOR_REPORT_REQUIRED")
        for report in (*self.reports, self.supervisor_report):
            if report.run_id != self.run_id or report.snapshot_hash != self.snapshot_hash:
                raise ValueError("REPORT_CYCLE_BINDING_MISMATCH")
            if report.created_at > self.created_at:
                raise ValueError("FUTURE_REPORT_REJECTED")
        if not all(set(row.evidence_hashes) <= set(self.evidence_hashes) for row in self.reports):
            raise ValueError("FOREIGN_CYCLE_EVIDENCE")
        if self.as_of > self.created_at:
            raise ValueError("FUTURE_SNAPSHOT_REJECTED")
        return self

    def presentation(self) -> list[dict[str, object]]:
        return [
            {
                "role": report.role.value,
                "label": LABELS[report.role],
                "status": report.status.value,
                "task": report.task,
                "report_hash": report.content_hash,
                "summary": report.summary,
                "evidence_count": len(report.evidence_hashes),
                "error_code": report.error_code,
            }
            for report in (self.supervisor_report, *self.reports)
        ]


class NayakDraft(Draft):
    status: Literal["ANSWERED", "ABSTAIN"]
    claims: tuple[InstitutionClaim, ...] = Field(min_length=1, max_length=3)


class NayakAnswer(Artifact):
    cycle_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    question: str = Field(min_length=1, max_length=1200)
    status: Literal["ANSWERED", "ABSTAIN", "REFUSED", "CANCELLED"]
    text: str = Field(min_length=1, max_length=2000)
    claims: tuple[InstitutionClaim, ...] = Field(max_length=3)
    report_hashes: tuple[str, ...] = Field(max_length=8)
    error_code: str | None = Field(default=None, max_length=100)
    execution_authority: Literal[False] = False

    @model_validator(mode="after")
    def cited_answer(self) -> Self:
        if self.status == "ANSWERED" and not self.claims:
            raise ValueError("ANSWER_REQUIRES_CITATIONS")
        if any(not set(row.evidence_hashes) <= set(self.report_hashes) for row in self.claims):
            raise ValueError("FOREIGN_ANSWER_REFERENCE")
        return self
