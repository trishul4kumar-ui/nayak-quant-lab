"""Novelty vs existing features and archived expressions. Train fold only."""

from __future__ import annotations

from datetime import datetime

from quantlab.alpha.ic import align_panels
from quantlab.discovery.definitions import NoveltyClass
from quantlab.discovery.evaluator import slice_panel
from quantlab.discovery.expression import ExprNode
from quantlab.features.engine import Panel
from quantlab.research.cross_section import spearman_ic


def novelty_class(
    expr: ExprNode,
    panel: Panel,
    references: dict[str, Panel],
    train_dates: list[datetime],
    archive_hashes: set[str],
) -> tuple[NoveltyClass, float]:
    if expr.identity_hash() in archive_hashes:
        return NoveltyClass.DUPLICATE, 1.0
    train = slice_panel(panel, train_dates)
    best = 0.0
    for ref in references.values():
        corr = _mean_abs_ic(train, slice_panel(ref, train_dates))
        if corr > best:
            best = corr
    if best >= 0.99:
        return NoveltyClass.DUPLICATE, best
    if best >= 0.85:
        return NoveltyClass.HIGH_REDUNDANCY, best
    if best >= 0.60:
        return NoveltyClass.MODERATE_REDUNDANCY, best
    if best >= 0.35:
        return NoveltyClass.LOW_REDUNDANCY, best
    return NoveltyClass.NOVEL, best


def _mean_abs_ic(left: Panel, right: Panel) -> float:
    aligned = align_panels(left, right)
    if not aligned:
        return 0.0
    vals: list[float] = []
    for a, b in aligned:
        ic = spearman_ic(a, b)
        if ic is not None:
            vals.append(abs(ic))
    return 0.0 if not vals else sum(vals) / len(vals)
