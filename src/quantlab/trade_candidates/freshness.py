"""Deterministic candidate freshness assessment; packets are never mutated."""

from quantlab.trade_candidates.models import (
    CandidateFreshness,
    CandidateFreshnessInput,
    CandidatePolicy,
    CandidateStatus,
    TradeCandidatePacket,
)


def assess_freshness(
    candidate: TradeCandidatePacket,
    current: CandidateFreshnessInput,
    policy: CandidatePolicy,
) -> CandidateFreshness:
    if candidate.candidate_hash != current.candidate_hash:
        raise ValueError("freshness input is for a different candidate")
    reasons: list[str] = []
    if current.created_at >= candidate.expires_at:
        reasons.append("CANDIDATE_TTL_EXPIRED")
    deviation = (
        abs(current.current_price - candidate.reference_price)
        / candidate.reference_price
        * 10_000
    )
    if deviation > policy.maximum_price_deviation_bps:
        reasons.append("PRICE_DEVIATION")
    if policy.require_fresh_regime and current.current_regime != candidate.reference_regime:
        reasons.append("REGIME_CHANGED")
    if policy.require_liquidity and current.liquidity_status is not current.liquidity_status.PASS:
        reasons.append("LIQUIDITY_NOT_PASS")
    if current.security_mapping_hash != candidate.security_mapping_hash:
        reasons.append("SECURITY_MAPPING_CHANGED")
    if current.corporate_action_hash != candidate.corporate_action_hash:
        reasons.append("CORPORATE_ACTION_CHANGED")
    if current.validation_expired:
        reasons.append("VALIDATION_EXPIRED")
    return CandidateFreshness(
        created_at=current.created_at,
        schema_version="trade-candidates-v1",
        candidate_hash=candidate.candidate_hash,
        status=CandidateStatus.EXPIRED if "CANDIDATE_TTL_EXPIRED" in reasons else (
            CandidateStatus.BLOCKED if reasons else CandidateStatus.READY_FOR_REVIEW
        ),
        reasons=tuple(reasons),
    )
