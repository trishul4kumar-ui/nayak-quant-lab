"""Syntactic similarity. Statistical independence is not inferred from text difference."""

from __future__ import annotations

from quantlab.discovery.expression import ExprNode
from quantlab.discovery.redundancy import feature_overlap
from quantlab.knowledge.entities import NoveltyHint, SimilarityClass

_RANK = {
    SimilarityClass.IDENTICAL: 5,
    SimilarityClass.HIGH_REDUNDANCY: 4,
    SimilarityClass.RELATED: 3,
    SimilarityClass.WEAKLY_RELATED: 2,
    SimilarityClass.DISTINCT: 1,
    SimilarityClass.UNKNOWN: 0,
}


def expression_similarity(left: ExprNode, right: ExprNode) -> SimilarityClass:
    if left.identity_hash() == right.identity_hash():
        return SimilarityClass.IDENTICAL
    overlap = feature_overlap(left, right)
    if overlap >= 0.99:
        return SimilarityClass.HIGH_REDUNDANCY
    if overlap >= 0.5:
        return SimilarityClass.RELATED
    if overlap > 0:
        return SimilarityClass.WEAKLY_RELATED
    if not left.feature_names() or not right.feature_names():
        return SimilarityClass.UNKNOWN
    return SimilarityClass.DISTINCT


def novelty_hint(expr: ExprNode, archive: list[ExprNode]) -> NoveltyHint:
    if not archive:
        return NoveltyHint.UNKNOWN
    best = SimilarityClass.DISTINCT
    for peer in archive:
        klass = expression_similarity(expr, peer)
        if _RANK[klass] > _RANK[best]:
            best = klass
    if best is SimilarityClass.IDENTICAL:
        return NoveltyHint.KNOWN
    if best in {SimilarityClass.HIGH_REDUNDANCY, SimilarityClass.RELATED}:
        return NoveltyHint.RELATED
    if best is SimilarityClass.UNKNOWN:
        return NoveltyHint.UNKNOWN
    return NoveltyHint.NOVEL
