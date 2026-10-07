"""Pure candidate assembly. No broker, sizing or provider access is permitted."""

from datetime import UTC, datetime

from quantlab.agents.contracts import EvidenceStatus
from quantlab.agents.hashing import digest
from quantlab.trade_candidates.models import (
    CandidateBuildInput,
    CandidatePolicy,
    CandidateStatus,
    TradeCandidatePacket,
)

POLICY_TIME = datetime(2026, 10, 7, tzinfo=UTC)


def default_candidate_policy() -> CandidatePolicy:
    return CandidatePolicy(
        created_at=POLICY_TIME,
        schema_version="trade-candidates-v1",
        policy_id="45-v1",
        maximum_snapshot_age_seconds=300,
        maximum_price_deviation_bps=75,
    )


def build_candidate(
    value: CandidateBuildInput, policy: CandidatePolicy | None = None
) -> TradeCandidatePacket:
    value = value.verified()
    policy = (policy or default_candidate_policy()).verified()
    blockers = []
    not_tested = []
    for summary in value.summaries:
        if summary.status in {EvidenceStatus.FAIL, EvidenceStatus.UNKNOWN}:
            blockers.append(f"{summary.category}:{summary.status}")
        elif summary.status is EvidenceStatus.NOT_TESTED:
            not_tested.append(summary.category)
    if value.data_quality != "valid" or value.data_freshness != "fresh":
        blockers.append("DATA_NOT_FRESH_AND_VALID")
    if value.research_gate_result != "RESEARCH_CANDIDATE":
        blockers.append("RESEARCH_GATE_NOT_ELIGIBLE")
    if not_tested:
        blockers.append("REQUIRED_EVIDENCE_NOT_TESTED")
    candidate_id = digest(
        {
            "snapshot": value.snapshot_hash,
            "adjudication": value.adjudication_hash,
            "plan": value.level_plan_hash,
            "security": value.security_id,
        }
    )[:32]
    candidate_hash = digest(
        {
            "candidate_id": candidate_id,
            "snapshot_hash": value.snapshot_hash,
            "adjudication_hash": value.adjudication_hash,
            "level_plan_hash": value.level_plan_hash,
            "policy": policy.content_hash,
        }
    )
    return TradeCandidatePacket(
        created_at=value.created_at,
        schema_version="trade-candidates-v1",
        candidate_id=candidate_id,
        candidate_hash=candidate_hash,
        status=CandidateStatus.BLOCKED if blockers else CandidateStatus.READY_FOR_REVIEW,
        expires_at=value.expires_at,
        security_id=value.security_id,
        stance=value.stance,
        snapshot_hash=value.snapshot_hash,
        bull_memo_hash=value.bull_memo_hash,
        bear_memo_hash=value.bear_memo_hash,
        debate_hash=value.debate_hash,
        adjudication_hash=value.adjudication_hash,
        level_plan_hash=value.level_plan_hash,
        research_gate_hash=value.research_gate_hash,
        research_gate_result=value.research_gate_result,
        summaries=value.summaries,
        data_quality=value.data_quality,
        data_freshness=value.data_freshness,
        raw_bull_confidence=value.raw_bull_confidence,
        raw_bear_confidence=value.raw_bear_confidence,
        calibrated_confidence=value.calibrated_confidence,
        calibration_version=value.calibration_version,
        reference_price=value.reference_price,
        reference_regime=value.reference_regime,
        security_mapping_hash=value.security_mapping_hash,
        corporate_action_hash=value.corporate_action_hash,
        hard_blockers=tuple(sorted(set(blockers))),
        warnings=("CANDIDATE_IS_NOT_AN_ORDER", "RANKING_DOES_NOT_GRANT_EXECUTION_AUTHORITY"),
        not_tested=tuple(sorted(set(not_tested))),
        candidate_policy_hash=policy.content_hash,
    )
