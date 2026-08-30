"""Freeze MarketState(T) / snapshot(T). Future appends cannot mutate T."""

from __future__ import annotations

from datetime import datetime

from quantlab.core.identifiers import InstrumentId
from quantlab.core.time import PointInTime
from quantlab.domain.models import MarketState, PriceState
from quantlab.realtime_data import quality as quality_mod
from quantlab.realtime_data import sequence as sequence_mod
from quantlab.realtime_data import session as session_mod
from quantlab.realtime_data.freshness import classify as freshness_classify
from quantlab.realtime_data.hashing import iso, sha256
from quantlab.realtime_data.models import (
    FreshnessStatus,
    MarketObservation,
    QualityStatus,
    RealTimeSnapshot,
    SequenceKind,
)

SOURCE_MANIFEST = "mock-observe-only:v1"
SECURITY_MASTER = "nse-cm-synthetic-master-v1"


def freeze(
    observations: tuple[MarketObservation, ...],
    *,
    as_of: datetime,
    halted: bool = False,
) -> RealTimeSnapshot:
    allowed = tuple(row for row in observations if row.event_time <= as_of)
    qualities = [quality_mod.classify(row) for row in allowed]
    overall_q = _worst_quality(qualities) if qualities else QualityStatus.MISSING
    seq = SequenceKind.VALID
    previous: MarketObservation | None = None
    for row in allowed:
        kind = sequence_mod.classify(previous, row)
        if kind is not SequenceKind.VALID:
            seq = kind
            break
        previous = row
    freshness = FreshnessStatus.UNKNOWN
    if allowed:
        last = allowed[-1]
        freshness = freshness_classify(last, now=as_of)
    session = session_mod.classify(as_of, halted=halted)
    payload = {
        "as_of": iso(as_of),
        "obs": [row.payload_hash for row in allowed],
        "quality": overall_q.value,
        "sequence": seq.value,
        "calendar": session_mod.calendar_version(),
        "source": SOURCE_MANIFEST,
        "master": SECURITY_MASTER,
        "schema": "3.1.0",
    }
    snapshot_hash = sha256(payload)
    names = {row.security_id for row in allowed}
    return RealTimeSnapshot(
        snapshot_id=f"rt-{snapshot_hash[:12]}",
        snapshot_hash=snapshot_hash,
        source_manifest_hash=sha256(SOURCE_MANIFEST),
        security_master_hash=sha256(SECURITY_MASTER),
        calendar_version=session_mod.calendar_version(),
        as_of=as_of,
        observations=allowed,
        quality=overall_q,
        freshness=freshness,
        session=session,
        sequence_kind=seq,
        n_names=len(names),
        extras={"future_ignored": len(observations) - len(allowed)},
    )


def to_market_states(snapshot: RealTimeSnapshot) -> tuple[MarketState, ...]:
    states: list[MarketState] = []
    for row in snapshot.observations:
        if row.price is None:
            continue
        identity = InstrumentId.parse(row.security_id)
        pit = PointInTime(
            event_time=row.event_time,
            effective_time=row.event_time,
            available_time=row.receive_time,
            ingestion_time=row.processing_time,
        )
        states.append(
            MarketState(
                instrument=identity,
                as_of=snapshot.as_of,
                pit=pit,
                price=PriceState(close=row.price),
            )
        )
    return tuple(states)


def _worst_quality(values: list[QualityStatus]) -> QualityStatus:
    rank = {
        QualityStatus.VALID: 0,
        QualityStatus.DEGRADED: 1,
        QualityStatus.STALE: 2,
        QualityStatus.MISSING: 3,
        QualityStatus.INVALID: 4,
        QualityStatus.DISCONNECTED: 5,
        QualityStatus.UNKNOWN: 6,
    }
    return max(values, key=lambda item: rank[item])
