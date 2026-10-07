"""Attention ranking only. Scores never authorize paper or live execution."""

from quantlab.trade_candidates.models import CandidateStatus, TradeCandidatePacket


def attention_score(candidate: TradeCandidatePacket) -> float:
    """Unknown/incomplete candidates rank below review-ready candidates."""
    if candidate.status is not CandidateStatus.READY_FOR_REVIEW or candidate.hard_blockers:
        return -1.0
    confidence = candidate.calibrated_confidence
    if confidence is None:
        confidence = min(candidate.raw_bull_confidence, candidate.raw_bear_confidence)
    return round(confidence, 8)


def rank_for_review(
    candidates: tuple[TradeCandidatePacket, ...],
) -> tuple[TradeCandidatePacket, ...]:
    return tuple(
        sorted(
            candidates,
            key=lambda item: (attention_score(item), item.content_hash),
            reverse=True,
        )
    )
