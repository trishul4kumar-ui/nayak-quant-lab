"""Quality classification. Stale/invalid/missing never silently become valid."""

from __future__ import annotations

from quantlab.realtime_data.models import MarketObservation, QualityStatus


def classify(observation: MarketObservation) -> QualityStatus:
    if observation.quality is QualityStatus.DISCONNECTED:
        return QualityStatus.DISCONNECTED
    if observation.price is None or observation.price <= 0:
        return QualityStatus.INVALID
    if observation.quality is QualityStatus.STALE:
        return QualityStatus.STALE
    if observation.quality is QualityStatus.MISSING:
        return QualityStatus.MISSING
    if observation.quality is QualityStatus.DEGRADED:
        return QualityStatus.DEGRADED
    if observation.quality is QualityStatus.VALID:
        return QualityStatus.VALID
    return QualityStatus.UNKNOWN


def never_upgrade(current: QualityStatus, claimed: QualityStatus) -> QualityStatus:
    """A worse status cannot be silently upgraded to VALID."""
    rank = {
        QualityStatus.VALID: 0,
        QualityStatus.DEGRADED: 1,
        QualityStatus.STALE: 2,
        QualityStatus.MISSING: 3,
        QualityStatus.INVALID: 4,
        QualityStatus.DISCONNECTED: 5,
        QualityStatus.UNKNOWN: 6,
    }
    return current if rank[current] >= rank[claimed] else claimed
