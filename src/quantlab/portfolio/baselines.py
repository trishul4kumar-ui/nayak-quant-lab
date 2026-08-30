"""Transparent portfolio constructors. These are the control experiments."""

from __future__ import annotations

import math

from quantlab.core.errors import AlignmentError
from quantlab.core.identifiers import InstrumentId
from quantlab.domain.models import Signal, TargetPosition
from quantlab.math.metrics import cross_sectional_ranks
from quantlab.portfolio.optimize import EqualWeight, RankTopNLong


def _finite(scores: dict[str, float]) -> dict[str, float]:
    out: dict[str, float] = {}
    seen: set[str] = set()
    for key, value in scores.items():
        if not math.isfinite(value):
            raise AlignmentError(f"non-finite score for {key}")
        parsed = str(InstrumentId.parse(key))
        if parsed in seen:
            raise AlignmentError(f"duplicate security_id {parsed}")
        seen.add(parsed)
        out[parsed] = value
    return out


def top_n_equal(
    scores: dict[str, float], top_n: int, require_positive: bool = True
) -> list[TargetPosition]:
    clean = _finite(scores)
    signals = _as_signals(clean)
    return RankTopNLong(top_n=top_n, require_positive=require_positive).weights(signals)


def bottom_n_equal(scores: dict[str, float], bottom_n: int) -> list[TargetPosition]:
    inverted = {key: -value for key, value in _finite(scores).items()}
    return top_n_equal(inverted, bottom_n, require_positive=False)


def long_short_top_bottom(
    scores: dict[str, float],
    top_n: int,
    bottom_n: int,
) -> list[TargetPosition]:
    longs = top_n_equal(scores, top_n, require_positive=False)
    shorts = bottom_n_equal(scores, bottom_n)
    long_w = 0.5 / max(len(longs), 1)
    short_w = -0.5 / max(len(shorts), 1)
    out = [TargetPosition(instrument=t.instrument, weight=long_w) for t in longs]
    out.extend(TargetPosition(instrument=t.instrument, weight=short_w) for t in shorts)
    return out


def equal_weight_names(scores: dict[str, float]) -> list[TargetPosition]:
    return EqualWeight().weights(_as_signals(_finite(scores)))


def rank_weight(scores: dict[str, float]) -> list[TargetPosition]:
    """w_i ∝ max(rank_i, 0) after mapping ranks to [0, 1]; long-only."""
    clean = _finite(scores)
    ranks = cross_sectional_ranks(clean)
    positive = {k: v for k, v in ranks.items() if v > 0}
    total = sum(positive.values())
    if total <= 0:
        return []
    return [
        TargetPosition(instrument=InstrumentId.parse(k), weight=v / total)
        for k, v in positive.items()
    ]


def score_weight(scores: dict[str, float]) -> list[TargetPosition]:
    """w_i ∝ max(score_i, 0). Clipping of negatives is recorded by dropping them."""
    clean = _finite(scores)
    positive = {k: v for k, v in clean.items() if v > 0}
    total = sum(positive.values())
    if total <= 0:
        return []
    return [
        TargetPosition(instrument=InstrumentId.parse(k), weight=v / total)
        for k, v in positive.items()
    ]


def _as_signals(scores: dict[str, float]) -> list[Signal]:
    from datetime import UTC, datetime

    as_of = datetime(2024, 1, 1, tzinfo=UTC)
    return [
        Signal(instrument=InstrumentId.parse(key), score=value, as_of=as_of)
        for key, value in scores.items()
    ]


def targets_to_map(targets: list[TargetPosition]) -> dict[str, float]:
    out: dict[str, float] = {}
    for target in targets:
        key = str(target.instrument)
        if key in out:
            raise AlignmentError(f"duplicate security_id {key}")
        out[key] = target.weight
    return out
