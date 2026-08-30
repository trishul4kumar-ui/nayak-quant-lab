"""Sequence integrity. Duplicates and gaps are first-class, not hidden."""

from __future__ import annotations

from quantlab.realtime_data.models import MarketObservation, SequenceKind


def classify(
    previous: MarketObservation | None,
    current: MarketObservation,
) -> SequenceKind:
    if current.sequence is None:
        return SequenceKind.UNKNOWN
    if previous is None:
        return SequenceKind.VALID
    if previous.sequence is None:
        return SequenceKind.UNKNOWN
    if current.sequence == previous.sequence:
        return SequenceKind.DUPLICATE
    if current.sequence == previous.sequence + 1:
        return SequenceKind.VALID
    if current.sequence > previous.sequence + 1:
        return SequenceKind.GAP
    return SequenceKind.OUT_OF_ORDER
