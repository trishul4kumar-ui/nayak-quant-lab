"""Trailing-window operators. No centered windows, no future bars."""

from __future__ import annotations

from quantlab.domain.models import OHLCVBar
from quantlab.math.metrics import realized_vol, simple_returns, zscore


def price_field(bar: OHLCVBar, field: str) -> float:
    if field == "close":
        return bar.close
    if field == "open":
        return bar.open
    if field == "high":
        return bar.high
    if field == "low":
        return bar.low
    if field == "volume":
        return float(bar.volume)
    raise ValueError(f"unsupported price field: {field}")


def trailing_return(prices: list[float], lookback: int) -> float | None:
    """close[t]/close[t-N]-1. Identical to MarketState momentum_N."""
    if lookback < 1 or len(prices) < lookback + 1:
        return None
    base = prices[-1 - lookback]
    last = prices[-1]
    if base <= 0:
        return None
    return last / base - 1.0


def rolling_mean(values: list[float], lookback: int) -> float | None:
    if lookback < 1 or len(values) < lookback:
        return None
    window = values[-lookback:]
    return sum(window) / len(window)


def rolling_std_of_returns(prices: list[float], lookback: int) -> float | None:
    rets = simple_returns(prices)
    if lookback < 1 or len(rets) < lookback:
        return None
    return realized_vol(rets[-lookback:])


def trailing_zscore(values: list[float], lookback: int) -> float | None:
    if lookback < 2 or len(values) < lookback:
        return None
    scaled = zscore(values[-lookback:])
    return scaled[-1]


def high_low_range(bar: OHLCVBar) -> float | None:
    if bar.close <= 0:
        return None
    return (bar.high - bar.low) / bar.close


def close_to_high(bar: OHLCVBar) -> float | None:
    if bar.high <= 0:
        return None
    return bar.close / bar.high - 1.0


def close_to_low(bar: OHLCVBar) -> float | None:
    if bar.low <= 0:
        return None
    return bar.close / bar.low - 1.0


def volume_change(volumes: list[float]) -> float | None:
    if len(volumes) < 2 or volumes[-2] <= 0:
        return None
    return volumes[-1] / volumes[-2] - 1.0


def dollar_turnover_ratio(closes: list[float], volumes: list[float], lookback: int) -> float | None:
    if lookback < 1 or len(closes) < lookback or len(volumes) < lookback:
        return None
    dollars = [closes[i] * volumes[i] for i in range(-lookback, 0)]
    mean = sum(dollars) / len(dollars)
    if mean <= 0:
        return None
    return dollars[-1] / mean
