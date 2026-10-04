from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from quantlab.backtest.spec import config_hash
from quantlab.core.identifiers import InstrumentId
from quantlab.domain.models import OHLCVBar, StrategyContext
from quantlab.market.state import build_cross_section
from quantlab.math.metrics import max_drawdown as math_max_drawdown
from quantlab.math.metrics import summarize_equity
from quantlab.portfolio.construction import construct_portfolio
from quantlab.portfolio.turnover import two_sided_turnover
from quantlab.research.strategy import Strategy
from quantlab.risk.firewall import RiskFirewall


class BacktestConfig(BaseModel):
    lookback: int = 20
    cost_bps: float = 10.0
    initial_equity: float = 1_000_000.0
    slippage_bps: float = 0.0
    fill_policy: str = "next_bar"
    eval_start: datetime | None = None
    eval_end: datetime | None = None
    seed: int = 0

    @field_validator("fill_policy")
    @classmethod
    def _fill(cls, value: str) -> str:
        if value != "next_bar":
            raise ValueError("only next_bar fills are implemented (ADR-005)")
        return value

    @field_validator("cost_bps", "slippage_bps", "initial_equity")
    @classmethod
    def _non_negative(cls, value: float) -> float:
        if value < 0:
            raise ValueError("cost, slippage, and equity cannot be negative")
        return value

    def identity(self) -> str:
        return config_hash(self.model_dump(mode="json"))


class BacktestResult(BaseModel):
    equity_curve: list[float]
    dates: list[datetime]
    turnover: list[float]
    total_return: float
    max_drawdown: float
    n_rebalances: int
    cost_drag: float
    metrics: dict[str, float] = Field(default_factory=dict)
    integrity: dict[str, str] = Field(default_factory=dict)
    market_states_used: int = 0
    ending_equity: float = 0.0
    initial_equity: float = 1_000_000.0
    n_trades: int = 0
    config_hash: str = ""


def run_backtest(
    bars_by_instrument: dict[InstrumentId, list[OHLCVBar]],
    strategy: Strategy,
    firewall: RiskFirewall,
    config: BacktestConfig | None = None,
) -> BacktestResult:
    """Signal at t earns return t → t+1. No same-bar fill (ADR-005)."""
    cfg = config or BacktestConfig()
    calendar = _shared_calendar(bars_by_instrument)
    close_px = _close_map(bars_by_instrument)
    equity = cfg.initial_equity
    curve: list[float] = []
    dates: list[datetime] = []
    turnovers: list[float] = []
    prev_weights: dict[str, float] = {}
    cost_paid = 0.0
    rebalances = 0
    states_used = 0
    n_trades = 0
    charge_bps = cfg.cost_bps + cfg.slippage_bps
    gross_sum = 0.0
    net_sum = 0.0

    for i in range(cfg.lookback + 1, len(calendar) - 1):
        as_of = calendar[i]
        nxt = calendar[i + 1]
        if cfg.eval_start is not None and as_of < cfg.eval_start:
            continue
        if cfg.eval_end is not None and as_of > cfg.eval_end:
            continue
        context_bars: list[OHLCVBar] = []
        for series in bars_by_instrument.values():
            context_bars.extend(b for b in series if b.pit.is_available_at(as_of))
        states = build_cross_section(bars_by_instrument, as_of, cfg.lookback)
        states_used += len(states)

        ctx = StrategyContext(as_of=as_of, bars=context_bars, market_states=states)
        strategy.on_start(ctx)
        signals = strategy.generate_signals(ctx)
        proposal = construct_portfolio(strategy, signals, as_of, reason="cs_momentum")
        authorized = firewall.require(proposal)
        weights = {str(t.instrument): t.weight for t in authorized.targets}
        turnover = _turnover(prev_weights, weights)
        cost = equity * turnover * (charge_bps / 10_000.0)
        equity -= cost
        cost_paid += cost
        port_ret = _portfolio_return(weights, close_px, as_of, nxt)
        equity *= 1.0 + port_ret
        curve.append(equity)
        dates.append(nxt)
        turnovers.append(turnover)
        prev_weights = weights
        rebalances += 1
        gross_sum += sum(abs(w) for w in weights.values())
        net_sum += sum(weights.values())
        if turnover > 0:
            n_trades += 1

    cost_drag = cost_paid / cfg.initial_equity if cfg.initial_equity else 0.0
    metrics = summarize_equity(curve, turnovers, cost_drag)
    if rebalances:
        metrics["mean_gross"] = gross_sum / rebalances
        metrics["mean_net"] = net_sum / rebalances
        metrics["mean_cash"] = 1.0 - metrics["mean_net"]
    total_return = metrics["total_return"]
    ending = curve[-1] if curve else cfg.initial_equity
    return BacktestResult(
        equity_curve=curve,
        dates=dates,
        turnover=turnovers,
        total_return=total_return,
        max_drawdown=math_max_drawdown(curve),
        n_rebalances=rebalances,
        cost_drag=cost_drag,
        metrics=metrics,
        integrity={},
        market_states_used=states_used,
        ending_equity=ending,
        initial_equity=cfg.initial_equity,
        n_trades=n_trades,
        config_hash=cfg.identity(),
    )


def shared_calendar(bars: dict[InstrumentId, list[OHLCVBar]]) -> list[datetime]:
    """Return the exchange/session timeline, not an all-instrument intersection.

    Universe membership and per-security availability are evaluated at each
    session by ``build_cross_section``.  Requiring every instrument to print on
    every date silently deleted valid market sessions whenever an IPO, delisting,
    suspension, or temporary data gap occurred.
    """
    sessions = {bar.pit.event_time for series in bars.values() for bar in series}
    return sorted(sessions)


def _shared_calendar(bars: dict[InstrumentId, list[OHLCVBar]]) -> list[datetime]:
    return shared_calendar(bars)


def _close_map(
    bars: dict[InstrumentId, list[OHLCVBar]],
) -> dict[tuple[str, datetime], float]:
    """Earliest-available print for each event. Late restatements do not overwrite."""
    out: dict[tuple[str, datetime], float] = {}
    seen_available: dict[tuple[str, datetime], datetime] = {}
    for inst, series in bars.items():
        ordered = sorted(series, key=lambda b: b.pit.available_time)
        for bar in ordered:
            key = (str(inst), bar.pit.event_time)
            previous = seen_available.get(key)
            if previous is not None and bar.pit.available_time >= previous:
                continue
            out[key] = bar.close
            seen_available[key] = bar.pit.available_time
    return out


def _turnover(prev: dict[str, float], new: dict[str, float]) -> float:
    return two_sided_turnover(prev, new)


def _portfolio_return(
    weights: dict[str, float],
    close_px: dict[tuple[str, datetime], float],
    as_of: datetime,
    nxt: datetime,
) -> float:
    ret = 0.0
    for inst, w in weights.items():
        p0 = close_px.get((inst, as_of))
        p1 = close_px.get((inst, nxt))
        if p0 and p1 and p0 > 0:
            ret += w * (p1 / p0 - 1.0)
    return ret
