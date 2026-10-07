"""Pure review reduction. Deterministic exit conditions always dominate commentary."""

from typing import Literal

from quantlab.position_intelligence.models import (
    PositionAssessment,
    PositionReviewContext,
    PositionView,
    SuggestedStance,
)


def assess_position(
    context: PositionReviewContext,
    bull: PositionView,
    bear: PositionView,
) -> PositionAssessment:
    context, bull, bear = context.verified(), bull.verified(), bear.verified()
    if {bull.role, bear.role} != {"BULL", "BEAR"}:
        raise ValueError("independent Bull and Bear views are required")
    if bull.context_hash != context.content_hash or bear.context_hash != context.content_hash:
        raise ValueError("both views must use the same frozen review context")
    blockers: list[str] = []
    thesis: Literal["INTACT", "WEAKENING", "INVALIDATED", "UNKNOWN"]
    if context.position_closed:
        blockers.append("POSITION_ALREADY_CLOSED")
        stance = SuggestedStance.MORE_RESEARCH
        thesis = "UNKNOWN"
    elif context.market_freshness != "fresh":
        blockers.append("MARKET_STATE_NOT_FRESH")
        stance = SuggestedStance.MORE_RESEARCH
        thesis = "UNKNOWN"
    elif tuple(rule for rule in context.exit_rules if rule.triggered):
        stance = SuggestedStance.EXIT_CANDIDATE
        thesis = "INVALIDATED"
    elif "INVALIDATED" in {bull.thesis_status, bear.thesis_status}:
        stance = SuggestedStance.REDUCE_CANDIDATE
        thesis = "WEAKENING"
    elif "WEAKENING" in {bull.thesis_status, bear.thesis_status}:
        stance = SuggestedStance.MORE_RESEARCH
        thesis = "WEAKENING"
    else:
        stance = SuggestedStance.HOLD
        thesis = "INTACT"
    return PositionAssessment(
        created_at=context.created_at,
        schema_version="position-intelligence-v1",
        position_id=context.position_id,
        context_hash=context.content_hash,
        bull_view_hash=bull.content_hash,
        bear_view_hash=bear.content_hash,
        thesis_status=thesis,
        exit_rule_states=context.exit_rules,
        suggested_stance=stance,
        evidence_refs=tuple(sorted(set(bull.evidence_refs + bear.evidence_refs))),
        confidence=min(bull.confidence, bear.confidence),
        hard_blockers=tuple(blockers),
    )
