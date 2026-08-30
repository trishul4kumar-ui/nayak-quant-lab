"""PIT market snapshots for execution research. Missing ≠ 0."""

from __future__ import annotations

from datetime import datetime

from quantlab.core.errors import ExecutionResearchError
from quantlab.core.identifiers import InstrumentId
from quantlab.domain.models import OHLCVBar
from quantlab.math.metrics import simple_returns


def pit_bar(series: list[OHLCVBar], as_of: datetime) -> OHLCVBar | None:
    eligible = [bar for bar in series if bar.pit.available_time <= as_of]
    if not eligible:
        return None
    eligible.sort(key=lambda b: b.pit.event_time)
    return eligible[-1]


def pit_close(series: list[OHLCVBar], as_of: datetime) -> float | None:
    bar = pit_bar(series, as_of)
    if bar is None or bar.close <= 0:
        return None
    return float(bar.close)


def pit_volume(series: list[OHLCVBar], as_of: datetime) -> float | None:
    bar = pit_bar(series, as_of)
    if bar is None:
        return None
    return float(bar.volume)


def trailing_volume(series: list[OHLCVBar], as_of: datetime, lookback: int) -> float | None:
    eligible = [bar for bar in series if bar.pit.available_time <= as_of]
    if not eligible:
        return None
    eligible.sort(key=lambda b: b.pit.event_time)
    window = eligible[-lookback:]
    if not window:
        return None
    return sum(float(bar.volume) for bar in window) / float(len(window))


def trailing_vol(series: list[OHLCVBar], as_of: datetime, lookback: int) -> float | None:
    eligible = [bar for bar in series if bar.pit.available_time <= as_of]
    eligible.sort(key=lambda b: b.pit.event_time)
    closes = [float(bar.close) for bar in eligible if bar.close > 0]
    if len(closes) < max(lookback, 3):
        return None
    rets = simple_returns(closes[-lookback:])
    if len(rets) < 2:
        return None
    mean = sum(rets) / len(rets)
    var = sum((v - mean) ** 2 for v in rets) / len(rets)
    return float(var**0.5)


def require_name(bars: dict[InstrumentId, list[OHLCVBar]], security_id: str) -> list[OHLCVBar]:
    for inst, series in bars.items():
        if str(inst) == security_id:
            return series
    raise ExecutionResearchError(f"unknown security {security_id}")
