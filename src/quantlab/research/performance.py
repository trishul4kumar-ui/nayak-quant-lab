"""Typed performance analytics over a backtest result."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from quantlab.backtest.engine import BacktestResult
from quantlab.math.annualization import DEFAULT_ANNUALIZATION, Annualization
from quantlab.math.drawdown import DrawdownEpisode, average_drawdown, top_drawdowns
from quantlab.math.metrics import simple_returns


class PerformanceReport(BaseModel):
    schema_version: str = "1"
    annualization: Annualization = Field(default_factory=lambda: DEFAULT_ANNUALIZATION)
    total_return: float
    cagr: float
    volatility: float
    sharpe: float
    sortino: float
    calmar: float
    max_drawdown: float
    average_drawdown: float
    win_rate: float
    profit_factor: float
    mean_turnover: float
    cost_drag: float
    n_periods: float
    skewness: float
    excess_kurtosis: float
    tail_loss_5pct: float
    ending_equity: float
    initial_equity: float
    n_trades: int
    risk_free_convention: str = DEFAULT_ANNUALIZATION.risk_free_convention
    top_drawdowns: list[DrawdownEpisode] = Field(default_factory=list)
    period_start: datetime | None = None
    period_end: datetime | None = None


def performance_from_backtest(
    result: BacktestResult,
    annualization: Annualization | None = None,
) -> PerformanceReport:
    conv = annualization or DEFAULT_ANNUALIZATION
    metrics = result.metrics
    return PerformanceReport(
        annualization=conv,
        total_return=metrics.get("total_return", result.total_return),
        cagr=metrics.get("cagr", 0.0),
        volatility=metrics.get("volatility", 0.0),
        sharpe=metrics.get("sharpe", 0.0),
        sortino=metrics.get("sortino", 0.0),
        calmar=metrics.get("calmar", 0.0),
        max_drawdown=result.max_drawdown,
        average_drawdown=metrics.get("average_drawdown", average_drawdown(result.equity_curve)),
        win_rate=metrics.get("win_rate", 0.0),
        profit_factor=metrics.get("profit_factor", 0.0),
        mean_turnover=metrics.get("mean_turnover", 0.0),
        cost_drag=result.cost_drag,
        n_periods=metrics.get("n_periods", float(len(simple_returns(result.equity_curve)))),
        skewness=metrics.get("skewness", 0.0),
        excess_kurtosis=metrics.get("excess_kurtosis", 0.0),
        tail_loss_5pct=metrics.get("tail_loss_5pct", 0.0),
        ending_equity=result.ending_equity,
        initial_equity=result.initial_equity,
        n_trades=result.n_trades,
        top_drawdowns=top_drawdowns(result.equity_curve, n=5),
        period_start=result.dates[0] if result.dates else None,
        period_end=result.dates[-1] if result.dates else None,
    )


def subperiod_returns(
    dates: list[datetime],
    equity: list[float],
    *,
    bucket: str = "year",
) -> dict[str, float]:
    """Simple return by calendar bucket. Equity[i] corresponds to dates[i]."""
    if len(dates) != len(equity) or len(equity) < 2:
        return {}
    groups: dict[str, list[tuple[datetime, float]]] = {}
    for when, value in zip(dates, equity, strict=True):
        if bucket == "year":
            key = f"{when.year}"
        elif bucket == "month":
            key = f"{when.year}-{when.month:02d}"
        elif bucket == "quarter":
            key = f"{when.year}-Q{(when.month - 1) // 3 + 1}"
        else:
            raise ValueError(f"unknown bucket {bucket}")
        groups.setdefault(key, []).append((when, value))
    out: dict[str, float] = {}
    for key, rows in groups.items():
        if len(rows) < 2 or rows[0][1] <= 0:
            continue
        out[key] = rows[-1][1] / rows[0][1] - 1.0
    return out
