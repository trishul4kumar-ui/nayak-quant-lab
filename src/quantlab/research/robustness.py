"""Cost, parameter, and regime robustness. Fragile peaks are warnings, not alpha."""

from __future__ import annotations

from pydantic import BaseModel, Field

from quantlab.backtest.costs import RESEARCH_COST_GRID_BPS
from quantlab.backtest.engine import BacktestConfig, BacktestResult, run_backtest
from quantlab.core.identifiers import InstrumentId
from quantlab.domain.models import OHLCVBar
from quantlab.math.metrics import simple_returns, summarize_equity
from quantlab.research.momentum import CrossSectionalMomentum
from quantlab.risk.firewall import RiskFirewall


class CostPoint(BaseModel):
    cost_bps: float
    sharpe: float
    total_return: float
    max_drawdown: float


class ParameterPoint(BaseModel):
    lookback: int
    sharpe: float
    total_return: float
    max_drawdown: float


class RegimeSlice(BaseModel):
    name: str
    methodology: str
    n: int
    total_return: float
    sharpe: float
    max_drawdown: float
    mean_turnover: float


class RobustnessReport(BaseModel):
    schema_version: str = "1"
    cost_points: list[CostPoint] = Field(default_factory=list)
    parameter_points: list[ParameterPoint] = Field(default_factory=list)
    fragile_parameter: bool = False
    regimes: list[RegimeSlice] = Field(default_factory=list)
    regime_methodology: str = (
        "bull/bear = equity above/below its median; high/low vol = |r| vs median |r|"
    )


def cost_sensitivity(
    bars: dict[InstrumentId, list[OHLCVBar]],
    strategy: CrossSectionalMomentum,
    firewall: RiskFirewall,
    lookback: int,
    grid: tuple[float, ...] = RESEARCH_COST_GRID_BPS,
) -> list[CostPoint]:
    points: list[CostPoint] = []
    for cost in grid:
        result = run_backtest(
            bars, strategy, firewall, BacktestConfig(lookback=lookback, cost_bps=cost)
        )
        points.append(
            CostPoint(
                cost_bps=cost,
                sharpe=result.metrics.get("sharpe", 0.0),
                total_return=result.total_return,
                max_drawdown=result.max_drawdown,
            )
        )
    return points


def parameter_surface(
    bars: dict[InstrumentId, list[OHLCVBar]],
    firewall: RiskFirewall,
    lookbacks: tuple[int, ...],
    *,
    top_n: int,
    cost_bps: float,
) -> list[ParameterPoint]:
    points: list[ParameterPoint] = []
    for lookback in lookbacks:
        strategy = CrossSectionalMomentum(lookback=lookback, top_n=top_n)
        result = run_backtest(
            bars, strategy, firewall, BacktestConfig(lookback=lookback, cost_bps=cost_bps)
        )
        points.append(
            ParameterPoint(
                lookback=lookback,
                sharpe=result.metrics.get("sharpe", 0.0),
                total_return=result.total_return,
                max_drawdown=result.max_drawdown,
            )
        )
    return points


def is_fragile(points: list[ParameterPoint], drop: float = 0.5) -> bool:
    if len(points) < 3:
        return False
    ordered = sorted(points, key=lambda p: p.lookback)
    best_i = max(range(len(ordered)), key=lambda i: ordered[i].sharpe)
    best = ordered[best_i].sharpe
    if best <= 0:
        return False
    neighbors: list[float] = []
    if best_i > 0:
        neighbors.append(ordered[best_i - 1].sharpe)
    if best_i + 1 < len(ordered):
        neighbors.append(ordered[best_i + 1].sharpe)
    if not neighbors:
        return False
    return all(n <= best * (1.0 - drop) for n in neighbors)


def regime_slices(result: BacktestResult) -> list[RegimeSlice]:
    """Equity-curve median split of a backtest (Prompt 05). Not the Prompt 09 detector."""
    equity = result.equity_curve
    if len(equity) < 8:
        return []
    rets = simple_returns(equity)
    median_eq = sorted(equity)[len(equity) // 2]
    abs_r = [abs(r) for r in rets]
    med_vol = sorted(abs_r)[len(abs_r) // 2]

    def _slice(name: str, mask: list[bool], methodology: str) -> RegimeSlice | None:
        idx = [i for i, flag in enumerate(mask) if flag]
        if len(idx) < 3:
            return None
        sub_eq = [equity[0]] + [equity[i + 1] for i in idx if i + 1 < len(equity)]
        if len(sub_eq) < 2:
            return None
        metrics = summarize_equity(
            sub_eq, [result.turnover[i] for i in idx if i < len(result.turnover)], 0.0
        )
        return RegimeSlice(
            name=name,
            methodology=methodology,
            n=len(idx),
            total_return=metrics["total_return"],
            sharpe=metrics["sharpe"],
            max_drawdown=metrics["max_drawdown"],
            mean_turnover=metrics["mean_turnover"],
        )

    bull_mask = [e >= median_eq for e in equity[:-1]]
    bear_mask = [not f for f in bull_mask]
    high_vol = [a >= med_vol for a in abs_r]
    low_vol = [not f for f in high_vol]
    method = "median split of this backtest's own equity/|return|; not an objective taxonomy"
    out: list[RegimeSlice] = []
    for name, mask in (
        ("bull", bull_mask),
        ("bear", bear_mask),
        ("high_vol", high_vol),
        ("low_vol", low_vol),
    ):
        item = _slice(name, mask, method)
        if item is not None:
            out.append(item)
    return out
