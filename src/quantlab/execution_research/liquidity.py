"""PIT liquidity profile. Synthetic bar volume is not official NSE ADV."""

from __future__ import annotations

from datetime import datetime

from quantlab.core.identifiers import InstrumentId
from quantlab.domain.models import OHLCVBar
from quantlab.execution_research.definition import LiquidityKind, LiquidityProfile
from quantlab.execution_research.market import pit_volume, trailing_volume


def liquidity_profile(
    series: list[OHLCVBar],
    *,
    security_id: str,
    as_of: datetime,
    max_participation: float,
    kind: LiquidityKind,
    lookback: int,
    use_future: bool = False,
) -> LiquidityProfile:
    if use_future:
        session = float(series[-1].volume) if series else None
        trailing = sum(float(b.volume) for b in series) / float(len(series)) if series else None
        return LiquidityProfile(
            security_id=security_id,
            as_of=as_of,
            session_volume=session,
            trailing_volume=trailing,
            participation_limit=max_participation,
            liquidity_bucket="lookahead",
            capacity_status="fail",
            note="future volume used; capacity_lookahead FAIL",
        )
    if kind is LiquidityKind.UNKNOWN:
        return LiquidityProfile(
            security_id=security_id,
            as_of=as_of,
            session_volume=None,
            trailing_volume=None,
            participation_limit=max_participation,
            liquidity_bucket="unknown",
            capacity_status="not_tested",
            note="volume unknown; capacity is NOT_TESTED, not infinite",
        )
    return LiquidityProfile(
        security_id=security_id,
        as_of=as_of,
        session_volume=pit_volume(series, as_of),
        trailing_volume=trailing_volume(series, as_of, lookback),
        participation_limit=max_participation,
        liquidity_bucket="synthetic",
        capacity_status="not_tested",
        note="synthetic bar volume is not official NSE ADV",
    )


def series_for(bars: dict[InstrumentId, list[OHLCVBar]], security_id: str) -> list[OHLCVBar]:
    for inst, series in bars.items():
        if str(inst) == security_id:
            return series
    return []
