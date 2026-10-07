"""Display-only indicators on provider candle closes. No signals or approvals."""

from __future__ import annotations

import math


def sma(values: list[float], period: int) -> list[float | None]:
    result: list[float | None] = [None] * len(values)
    for i in range(period - 1, len(values)):
        result[i] = sum(values[i - period + 1 : i + 1]) / period
    return result


def ema(values: list[float], period: int) -> list[float | None]:
    result: list[float | None] = [None] * len(values)
    if len(values) < period:
        return result
    value = sum(values[:period]) / period
    result[period - 1] = value
    alpha = 2 / (period + 1)
    for i in range(period, len(values)):
        value += alpha * (values[i] - value)
        result[i] = value
    return result


def bollinger(
    values: list[float], period: int = 20
) -> tuple[list[float | None], list[float | None]]:
    mid = sma(values, period)
    upper: list[float | None] = [None] * len(values)
    lower: list[float | None] = [None] * len(values)
    for i, average in enumerate(mid):
        if average is None:
            continue
        window = values[i - period + 1 : i + 1]
        sd = math.sqrt(sum((x - average) ** 2 for x in window) / period)
        upper[i], lower[i] = average + 2 * sd, average - 2 * sd
    return upper, lower


def rsi(values: list[float], period: int = 14) -> list[float | None]:
    result: list[float | None] = [None] * len(values)
    if len(values) <= period:
        return result
    changes = [b - a for a, b in zip(values, values[1:], strict=False)]
    gain = sum(max(x, 0) for x in changes[:period]) / period
    loss = sum(max(-x, 0) for x in changes[:period]) / period
    for i in range(period, len(values)):
        if i > period:
            delta = changes[i - 1]
            gain = (gain * (period - 1) + max(delta, 0)) / period
            loss = (loss * (period - 1) + max(-delta, 0)) / period
        result[i] = (
            50.0 if gain == loss == 0 else 100.0 if loss == 0 else (100 - 100 / (1 + gain / loss))
        )
    return result
