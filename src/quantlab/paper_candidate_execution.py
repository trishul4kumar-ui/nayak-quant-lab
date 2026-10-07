"""Candidate lineage bridge to the existing Paper OMS; no second OMS or broker route."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import Field

from quantlab.agents.hashing import Artifact
from quantlab.paper_oms.models import PaperOMSResult
from quantlab.trade_candidates.models import CandidateStatus, TradeCandidatePacket
from quantlab.trade_levels.models import LevelPlanStatus, TradeLevelPlan


class PaperMode(StrEnum):
    AUTO_PAPER_FROM_ELIGIBLE_CANDIDATE = "AUTO_PAPER_FROM_ELIGIBLE_CANDIDATE"
    HUMAN_APPROVED_PAPER = "HUMAN_APPROVED_PAPER"


class PaperEligibility(Artifact):
    candidate_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    level_plan_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    mode: PaperMode
    eligible: bool
    blockers: tuple[str, ...]
    execution_authority: Literal[False] = False


class PaperCandidateLineage(Artifact):
    """Maps a canonical Paper OMS result to frozen candidate evidence without changing OMS types."""

    candidate_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    level_plan_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    risk_decision_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    paper_oms_run_id: str = Field(min_length=1, max_length=160)
    paper_execution_model_version: str = Field(min_length=1, max_length=160)
    data_kind: Literal["PAPER"] = "PAPER"
    broker_write_enabled: Literal[False] = False


def link_paper_result(
    eligibility: PaperEligibility,
    result: PaperOMSResult,
    *,
    risk_decision_hash: str,
    execution_model_version: str,
    now: datetime,
) -> PaperCandidateLineage:
    """Attach lineage only after the canonical Paper OMS has produced a paper-only result."""
    if not eligibility.eligible or result.live_trading:
        raise ValueError("ineligible or non-paper result cannot receive candidate lineage")
    return PaperCandidateLineage(
        created_at=now,
        schema_version="paper-candidate-v1",
        candidate_hash=eligibility.candidate_hash,
        level_plan_hash=eligibility.level_plan_hash,
        risk_decision_hash=risk_decision_hash,
        paper_oms_run_id=result.run.oms_run_id,
        paper_execution_model_version=execution_model_version,
    )


def paper_eligibility(
    candidate: TradeCandidatePacket,
    plan: TradeLevelPlan,
    *,
    now: datetime,
    mode: PaperMode,
    human_approved: bool = False,
) -> PaperEligibility:
    blockers: list[str] = []
    if candidate.status not in {CandidateStatus.PAPER_ELIGIBLE, CandidateStatus.READY_FOR_REVIEW}:
        blockers.append("CANDIDATE_NOT_PAPER_ELIGIBLE")
    if candidate.expires_at <= now:
        blockers.append("CANDIDATE_STALE")
    if candidate.level_plan_hash != plan.content_hash:
        blockers.append("PLAN_LINEAGE_MISMATCH")
    if plan.status is not LevelPlanStatus.READY:
        blockers.append("NO_VALID_ENTRY")
    if mode is PaperMode.HUMAN_APPROVED_PAPER and not human_approved:
        blockers.append("HUMAN_PAPER_APPROVAL_REQUIRED")
    return PaperEligibility(
        created_at=now,
        schema_version="paper-candidate-v1",
        candidate_hash=candidate.content_hash,
        level_plan_hash=plan.content_hash,
        mode=mode,
        eligible=not blockers,
        blockers=tuple(blockers),
    )
