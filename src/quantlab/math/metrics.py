"""Deterministic mathematical primitives. No broker, UI, or LLM types."""

from __future__ import annotations

import math

import numpy as np

from quantlab.math.annualization import DEFAULT_ANNUALIZATION
from quantlab.math.drawdown import average_drawdown


def simple_returns(prices: list[float]) -> list[float]:
    if len(prices) < 2:
        return []
    arr = np.asarray(prices, dtype=np.float64)
    rel = arr[1:] / arr[:-1] - 1.0
    return [float(x) for x in rel.tolist()]


def log_returns(prices: list[float]) -> list[float]:
    if len(prices) < 2:
        return []
    arr = np.asarray(prices, dtype=np.float64)
    if np.any(arr <= 0):
        raise ValueError("log returns require positive prices")
    return [float(x) for x in np.diff(np.log(arr)).tolist()]


def zscore(values: list[float]) -> list[float]:
    if not values:
        return []
    arr = np.asarray(values, dtype=np.float64)
    std = float(arr.std(ddof=0))
    if std == 0.0:
        return [0.0] * len(values)
    return [float(x) for x in ((arr - arr.mean()) / std).tolist()]


def cross_sectional_ranks(values: dict[str, float]) -> dict[str, float]:
    """Average ranks in [0, 1]. Ties share the mean rank."""
    if not values:
        return {}
    items = list(values.items())
    scores = np.asarray([v[1] for v in items], dtype=np.float64)
    order = scores.argsort()
    ranks = np.empty(len(scores), dtype=np.float64)
    ranks[order] = np.arange(1, len(scores) + 1, dtype=np.float64)
    for value in np.unique(scores):
        mask = scores == value
        ranks[mask] = ranks[mask].mean()
    denom = max(len(scores) - 1, 1)
    scaled = (ranks - 1.0) / denom
    return {items[i][0]: float(scaled[i]) for i in range(len(items))}


def realized_vol(returns: list[float]) -> float | None:
    if len(returns) < 2:
        return None
    return float(np.std(np.asarray(returns, dtype=np.float64), ddof=0))


def max_drawdown(equity: list[float]) -> float:
    peak = 0.0
    max_dd = 0.0
    for value in equity:
        peak = max(peak, value)
        if peak > 0:
            max_dd = min(max_dd, value / peak - 1.0)
    return max_dd


def volatility(
    returns: list[float],
    periods_per_year: int = DEFAULT_ANNUALIZATION.sessions_per_year,
) -> float:
    if len(returns) < 2:
        return 0.0
    return float(
        np.std(np.asarray(returns, dtype=np.float64), ddof=0) * math.sqrt(periods_per_year)
    )


def cagr(
    equity: list[float],
    periods_per_year: int = DEFAULT_ANNUALIZATION.sessions_per_year,
) -> float:
    if len(equity) < 2 or equity[0] <= 0:
        return 0.0
    n = len(equity) - 1
    years = n / periods_per_year
    if years <= 0:
        return 0.0
    return float((equity[-1] / equity[0]) ** (1.0 / years) - 1.0)


def sharpe(
    returns: list[float],
    periods_per_year: int = DEFAULT_ANNUALIZATION.sessions_per_year,
    risk_free_per_period: float = 0.0,
) -> float:
    if len(returns) < 2:
        return 0.0
    arr = np.asarray(returns, dtype=np.float64)
    excess = arr - risk_free_per_period
    std = float(excess.std(ddof=0))
    if std == 0.0:
        return 0.0
    return float(excess.mean() / std * math.sqrt(periods_per_year))


def sortino(
    returns: list[float],
    periods_per_year: int = DEFAULT_ANNUALIZATION.sessions_per_year,
) -> float:
    if len(returns) < 2:
        return 0.0
    arr = np.asarray(returns, dtype=np.float64)
    downside = arr[arr < 0]
    if len(downside) == 0:
        return 0.0
    down_std = float(downside.std(ddof=0))
    if down_std == 0.0:
        return 0.0
    return float(arr.mean() / down_std * math.sqrt(periods_per_year))


def calmar(cagr_value: float, drawdown: float) -> float:
    if drawdown >= 0:
        return 0.0
    return float(cagr_value / abs(drawdown))


def win_rate(returns: list[float]) -> float:
    if not returns:
        return 0.0
    return float(sum(1 for r in returns if r > 0) / len(returns))


def profit_factor(returns: list[float]) -> float:
    gains = sum(r for r in returns if r > 0)
    losses = sum(r for r in returns if r < 0)
    if losses == 0:
        return 0.0 if gains == 0 else float("inf")
    return float(gains / abs(losses))


def mean_turnover(turnovers: list[float]) -> float:
    if not turnovers:
        return 0.0
    return float(sum(turnovers) / len(turnovers))


def skewness(returns: list[float]) -> float | None:
    if len(returns) < 3:
        return None
    arr = np.asarray(returns, dtype=np.float64)
    std = float(arr.std(ddof=0))
    if std == 0.0:
        return 0.0
    return float(np.mean(((arr - arr.mean()) / std) ** 3))


def excess_kurtosis(returns: list[float]) -> float | None:
    if len(returns) < 4:
        return None
    arr = np.asarray(returns, dtype=np.float64)
    std = float(arr.std(ddof=0))
    if std == 0.0:
        return 0.0
    return float(np.mean(((arr - arr.mean()) / std) ** 4) - 3.0)


def tail_loss(returns: list[float], quantile: float = 0.05) -> float | None:
    if not returns:
        return None
    if not 0.0 < quantile < 1.0:
        raise ValueError("quantile must be in (0, 1)")
    arr = np.asarray(returns, dtype=np.float64)
    return float(np.quantile(arr, quantile))


def summarize_equity(
    equity: list[float],
    turnovers: list[float],
    cost_drag: float,
    periods_per_year: int = DEFAULT_ANNUALIZATION.sessions_per_year,
) -> dict[str, float]:
    if len(equity) < 2:
        total = 0.0
        rets: list[float] = []
    else:
        total = equity[-1] / equity[0] - 1.0
        rets = simple_returns(equity)
    dd = max_drawdown(equity)
    cagr_value = cagr(equity, periods_per_year)
    pf = profit_factor(rets)
    if math.isinf(pf):
        pf = 0.0
    skew = skewness(rets)
    kurt = excess_kurtosis(rets)
    tail = tail_loss(rets)
    mt = mean_turnover(turnovers)
    holding = 0.0 if mt <= 0.0 else 1.0 / mt
    return {
        "total_return": total,
        "cagr": cagr_value,
        "volatility": volatility(rets, periods_per_year),
        "sharpe": sharpe(rets, periods_per_year),
        "sortino": sortino(rets, periods_per_year),
        "max_drawdown": dd,
        "average_drawdown": average_drawdown(equity),
        "calmar": calmar(cagr_value, dd),
        "win_rate": win_rate(rets),
        "profit_factor": pf,
        "mean_turnover": mt,
        "annual_turnover": mt * float(periods_per_year),
        "holding_period_sessions": holding,
        "cost_drag": cost_drag,
        "n_periods": float(len(rets)),
        "skewness": 0.0 if skew is None else skew,
        "excess_kurtosis": 0.0 if kurt is None else kurt,
        "tail_loss_5pct": 0.0 if tail is None else tail,
    }
