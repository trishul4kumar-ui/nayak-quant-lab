"""Deterministic assignment gate for the local research desk.

This module deliberately produces assignments or abstentions only.  It does not
invoke an LLM, call a tool, mutate a strategy, or import any broker/execution
module.  A future host may consume an ASSIGNED artifact only after applying its
own provider, tool, and release gates.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Literal, Self

from pydantic import Field, model_validator

from quantlab.agent_desk.models import DeskJob, DeskJobType
from quantlab.agents.contracts import EvidenceReference, EvidenceStatus
from quantlab.agents.hashing import Artifact


class DeskResearchRole(StrEnum):
    SUPERVISOR = "SUPERVISOR"
    BULL_ANALYST = "BULL_ANALYST"
    BEAR_ANALYST = "BEAR_ANALYST"
    DOCUMENT_NEWS_ANALYST = "DOCUMENT_NEWS_ANALYST"
    QUANT_ANALYST = "QUANT_ANALYST"
    RISK_OFFICER = "RISK_OFFICER"
    EXECUTION_MONITOR = "EXECUTION_MONITOR"
    AUDIT_COMPLIANCE = "AUDIT_COMPLIANCE"


class AssignmentDisposition(StrEnum):
    ASSIGNED = "ASSIGNED"
    ABSTAIN = "ABSTAIN"


_ROLE_BY_JOB = {
    DeskJobType.DATA_HEALTH: DeskResearchRole.SUPERVISOR,
    DeskJobType.UNIVERSE_REFRESH: DeskResearchRole.SUPERVISOR,
    DeskJobType.BULL_SCAN: DeskResearchRole.BULL_ANALYST,
    DeskJobType.BEAR_SCAN: DeskResearchRole.BEAR_ANALYST,
    DeskJobType.DOCUMENT_NEWS_REVIEW: DeskResearchRole.DOCUMENT_NEWS_ANALYST,
    DeskJobType.QUANT_RESEARCH: DeskResearchRole.QUANT_ANALYST,
    DeskJobType.RISK_REVIEW: DeskResearchRole.RISK_OFFICER,
    DeskJobType.EXECUTION_MONITOR: DeskResearchRole.EXECUTION_MONITOR,
    DeskJobType.AUDIT_EVIDENCE_REVIEW: DeskResearchRole.AUDIT_COMPLIANCE,
    DeskJobType.DEBATE: DeskResearchRole.SUPERVISOR,
    DeskJobType.CANDIDATE_REFRESH: DeskResearchRole.QUANT_ANALYST,
    DeskJobType.POSITION_REVIEW: DeskResearchRole.RISK_OFFICER,
    DeskJobType.DAILY_RECONCILIATION: DeskResearchRole.AUDIT_COMPLIANCE,
}

_MANDATES = {
    DeskResearchRole.SUPERVISOR: (
        "Route bounded research assignments and summarize frozen evidence."
    ),
    DeskResearchRole.BULL_ANALYST: "Find long-side hypotheses and supporting frozen evidence.",
    DeskResearchRole.BEAR_ANALYST: "Find downside, liquidity, regime, and invalidation evidence.",
    DeskResearchRole.DOCUMENT_NEWS_ANALYST: (
        "Summarize supplied frozen documents without treating narrative as proof."
    ),
    DeskResearchRole.QUANT_ANALYST: (
        "Run only approved deterministic research, validation, backtest, and TCA tools."
    ),
    DeskResearchRole.RISK_OFFICER: "Explain deterministic risk outputs and unresolved risk limits.",
    DeskResearchRole.EXECUTION_MONITOR: (
        "Observe orders, broker events, and reconciliation evidence without order authority."
    ),
    DeskResearchRole.AUDIT_COMPLIANCE: (
        "Assemble evidence packs, ledgers, and anomalies without certifying a release."
    ),
}


class SupervisorAssignment(Artifact):
    """A hash-bound, non-executing instruction for one research role."""

    assignment_id: str = Field(min_length=1, max_length=160)
    job_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    job_type: DeskJobType
    role: DeskResearchRole
    security_scope: tuple[str, ...] = Field(max_length=500)
    snapshot_hash: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    frozen_evidence: tuple[EvidenceReference, ...] = Field(max_length=500)
    disposition: AssignmentDisposition
    mandate: str = Field(min_length=1, max_length=500)
    claim_rule: str = (
        "Every material claim must cite the listed frozen evidence; unknown means abstain."
    )
    abstention_reason: str | None = Field(default=None, max_length=500)
    execution_authority: Literal[False] = False

    @model_validator(mode="after")
    def evidence_and_abstention_are_coherent(self) -> Self:
        if self.disposition is AssignmentDisposition.ASSIGNED:
            if self.snapshot_hash is None or not self.frozen_evidence:
                raise ValueError("assigned research requires a snapshot and frozen evidence")
            if any(item.snapshot_hash != self.snapshot_hash for item in self.frozen_evidence):
                raise ValueError("assigned research evidence must match the frozen snapshot")
            if any(
                item.status not in {EvidenceStatus.PASS, EvidenceStatus.WARN}
                for item in self.frozen_evidence
            ):
                raise ValueError("unknown, failed, or untested evidence requires abstention")
            if self.abstention_reason is not None:
                raise ValueError("assigned research cannot carry an abstention reason")
        elif not self.abstention_reason:
            raise ValueError("abstention requires a reason")
        return self


def route_research_job(
    job: DeskJob,
    evidence: tuple[EvidenceReference, ...],
    *,
    now: datetime,
) -> SupervisorAssignment:
    """Fail closed unless all supplied evidence is frozen, available, and usable.

    `evidence` is treated as data, never as routing instructions.  This keeps
    prompt-injection text in documents from changing the role, authority, or
    security scope selected by the supervisor.
    """
    role = _ROLE_BY_JOB[job.job_type]
    snapshot_hash = job.snapshot_dependency_hash
    relevant = tuple(item for item in evidence if item.snapshot_hash == snapshot_hash)
    reason = _abstention_reason(job, relevant, now=now)
    return SupervisorAssignment(
        created_at=now,
        assignment_id=f"assignment:{job.job_id}",
        job_hash=job.content_hash,
        job_type=job.job_type,
        role=role,
        security_scope=job.security_scope,
        snapshot_hash=snapshot_hash,
        frozen_evidence=relevant if reason is None else (),
        disposition=(
            AssignmentDisposition.ASSIGNED if reason is None else AssignmentDisposition.ABSTAIN
        ),
        mandate=_MANDATES[role],
        abstention_reason=reason,
    )


def _abstention_reason(
    job: DeskJob, evidence: tuple[EvidenceReference, ...], *, now: datetime
) -> str | None:
    if job.snapshot_dependency_hash is None:
        return "FROZEN_SNAPSHOT_REQUIRED"
    if not evidence:
        return "FROZEN_EVIDENCE_REQUIRED"
    if any(item.available_time > now for item in evidence):
        return "FUTURE_EVIDENCE_REJECTED"
    if any(item.status in {EvidenceStatus.UNKNOWN, EvidenceStatus.NOT_TESTED} for item in evidence):
        return "EVIDENCE_UNKNOWN"
    if any(item.status is EvidenceStatus.FAIL for item in evidence):
        return "EVIDENCE_FAILED"
    return None
