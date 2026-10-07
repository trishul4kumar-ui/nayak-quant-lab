from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from quantlab.agents.contracts import EvidenceStatus
from quantlab.agents.hashing import digest
from quantlab.trade_candidates.builder import build_candidate, default_candidate_policy
from quantlab.trade_candidates.freshness import assess_freshness
from quantlab.trade_candidates.lifecycle import ensure_transition
from quantlab.trade_candidates.models import (
    CandidateBuildInput,
    CandidateFreshnessInput,
    CandidateStatus,
    EvidenceSummary,
    ExposureStance,
)
from quantlab.trade_candidates.ranking import attention_score

NOW = datetime(2026, 10, 7, 7, tzinfo=UTC)


def summary(category: str, status: EvidenceStatus = EvidenceStatus.PASS) -> EvidenceSummary:
    return EvidenceSummary(
        created_at=NOW,
        schema_version="trade-candidates-v1",
        category=category,
        status=status,
        evidence_refs=(digest(category),),
        summary=f"Frozen {category} summary",
    )


def build_input(*, validation: EvidenceStatus = EvidenceStatus.PASS) -> CandidateBuildInput:
    return CandidateBuildInput(
        created_at=NOW,
        schema_version="trade-candidates-v1",
        security_id="NSE:EXAMPLE",
        stance=ExposureStance.LONG,
        expires_at=NOW + timedelta(minutes=5),
        snapshot_hash=digest("snapshot"),
        bull_memo_hash=digest("bull"),
        bear_memo_hash=digest("bear"),
        debate_hash=digest("debate"),
        adjudication_hash=digest("adjudication"),
        level_plan_hash=digest("levels"),
        research_gate_hash=digest("gate"),
        research_gate_result="RESEARCH_CANDIDATE",
        raw_bull_confidence=0.8,
        raw_bear_confidence=0.3,
        summaries=(
            summary("validation", validation),
            summary("features"),
            summary("factors"),
            summary("regime"),
            summary("liquidity_tca"),
            summary("portfolio_risk"),
        ),
        data_quality="valid",
        data_freshness="fresh",
        reference_price=100,
        reference_regime="TREND",
        security_mapping_hash=digest("mapping"),
    )


def test_complete_packet_is_deterministic_and_not_an_order() -> None:
    first = build_candidate(build_input())
    second = build_candidate(build_input())
    assert first == second
    assert first.status is CandidateStatus.READY_FOR_REVIEW
    assert attention_score(first) == 0.3
    with pytest.raises(ValidationError):
        type(first).model_validate({**first.model_dump(mode="python"), "quantity": 10})


def test_missing_or_not_tested_evidence_blocks_review() -> None:
    blocked = build_candidate(build_input(validation=EvidenceStatus.NOT_TESTED))
    assert blocked.status is CandidateStatus.BLOCKED
    assert "REQUIRED_EVIDENCE_NOT_TESTED" in blocked.hard_blockers
    assert attention_score(blocked) == -1


def test_freshness_blocks_price_regime_and_mapping_changes() -> None:
    candidate = build_candidate(build_input())
    current = CandidateFreshnessInput(
        created_at=NOW + timedelta(seconds=1),
        schema_version="trade-candidates-v1",
        candidate_hash=candidate.candidate_hash,
        current_price=102,
        current_regime="RANGE",
        liquidity_status=EvidenceStatus.PASS,
        security_mapping_hash=digest("different-mapping"),
    )
    result = assess_freshness(candidate, current, default_candidate_policy())
    assert result.status is CandidateStatus.BLOCKED
    assert set(result.reasons) == {"PRICE_DEVIATION", "REGIME_CHANGED", "SECURITY_MAPPING_CHANGED"}


def test_lifecycle_has_no_live_eligible_transition() -> None:
    ensure_transition(CandidateStatus.READY_FOR_REVIEW, CandidateStatus.PAPER_ELIGIBLE)
    with pytest.raises(ValueError):
        ensure_transition(CandidateStatus.BLOCKED, CandidateStatus.PAPER_ELIGIBLE)
