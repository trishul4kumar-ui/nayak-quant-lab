"""Research-grade validation suite around the existing next-bar engine.

This is not a second backtester. It answers whether an observed effect
survives costs, OOS windows, perturbation, and statistical scrutiny.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from quantlab.backtest.engine import (
    BacktestConfig,
    BacktestResult,
    run_backtest,
    shared_calendar,
)
from quantlab.backtest.spec import ResearchBacktestSpec
from quantlab.core.identifiers import InstrumentId
from quantlab.domain.models import Instrument, OHLCVBar, Signal, StrategyContext
from quantlab.market.state import build_cross_section
from quantlab.math.annualization import DEFAULT_ANNUALIZATION
from quantlab.math.metrics import sharpe, simple_returns
from quantlab.research.attribution import AttributionReport, empty_attribution
from quantlab.research.baselines import EqualWeightBaseline, RandomSignalBaseline
from quantlab.research.benchmarks import CashBenchmark, evaluate_benchmark
from quantlab.research.decay import DecayReport, signal_decay
from quantlab.research.envinfo import environment, git_dirty
from quantlab.research.gate import GateOutcome, ResearchGateResult, evaluate_research_gate
from quantlab.research.liquidity import LiquidityReport, evaluate_liquidity
from quantlab.research.momentum import CrossSectionalMomentum
from quantlab.research.multiple_testing import (
    CorrectionMethod,
    DeflatedSharpeReport,
    MultipleTestingReport,
    OverfittingReport,
    deflated_sharpe,
    evaluate_family,
    probability_of_backtest_overfitting,
)
from quantlab.research.performance import (
    PerformanceReport,
    performance_from_backtest,
    subperiod_returns,
)
from quantlab.research.robustness import (
    RobustnessReport,
    cost_sensitivity,
    is_fragile,
    parameter_surface,
    regime_slices,
)
from quantlab.research.statistics import StatisticalReport, evaluate_returns, sign_flip_p_value
from quantlab.research.walkforward import WalkForwardPlan, WindowKind, generate_walk_forward
from quantlab.risk.firewall import RiskFirewall, RiskLimits


class ValidationConfig(BaseModel):
    lookback: int = 20
    top_n: int = 2
    cost_bps: float = 10.0
    lookbacks: tuple[int, ...] = (10, 15, 20, 25, 30)
    train_sessions: int = 30
    test_sessions: int = 8
    step_sessions: int = 8
    embargo_sessions: int = 1
    label_horizon_sessions: int = 1
    window_kind: WindowKind = WindowKind.EXPANDING
    seed: int = 0
    n_boot: int = 200
    block_size: int = 5
    n_perm: int = 200
    family_id: str = "cs_momentum"
    slippage_model: str = "none"
    slippage_bps: float = 0.0


class WalkForwardEval(BaseModel):
    plan: WalkForwardPlan
    oos_sharpe: float | None = None
    oos_total_return: float | None = None
    window_returns: list[float] = Field(default_factory=list)
    windows_temporally_ok: bool = True


class ValidationReport(BaseModel):
    schema_version: str = "1"
    experiment_id: str = ""
    config_hash: str
    data_kind: str
    spec: ResearchBacktestSpec
    performance: PerformanceReport
    walk_forward: WalkForwardEval
    oos_windows: int
    oos_sharpe: float | None = None
    oos_total_return: float | None = None
    robustness: RobustnessReport
    statistics: StatisticalReport
    multiple_testing: MultipleTestingReport
    deflated_sharpe: DeflatedSharpeReport
    overfitting: OverfittingReport
    gate: ResearchGateResult
    benchmark: dict[str, object] = Field(default_factory=dict)
    attribution: AttributionReport
    decay: DecayReport
    liquidity: LiquidityReport
    subperiod: dict[str, float] = Field(default_factory=dict)
    baseline_sharpe: float | None = None
    random_baseline_sharpe: float | None = None
    validation_protocol: str = "next_bar_walk_forward_cost_adjusted"
    seed: int = 0
    git_dirty: bool = False
    python_version: str = ""
    integrity: dict[str, str] = Field(default_factory=dict)

    def as_str_map(self) -> dict[str, str]:
        return {
            "outcome": self.gate.outcome.value,
            "data_kind": self.data_kind,
            "config_hash": self.config_hash,
            "oos_windows": str(self.oos_windows),
            "oos_sharpe": "" if self.oos_sharpe is None else f"{self.oos_sharpe:.6f}",
            "fragile": str(self.robustness.fragile_parameter),
            "p_value": "" if self.statistics.p_value is None else f"{self.statistics.p_value:.6f}",
            "dsr": (
                ""
                if self.deflated_sharpe.deflated_sharpe is None
                else f"{self.deflated_sharpe.deflated_sharpe:.6f}"
            ),
            "pbo": self.overfitting.status.value,
            "protocol": self.validation_protocol,
        }


def run_validation_suite(
    bars: dict[InstrumentId, list[OHLCVBar]],
    instruments: list[Instrument],
    *,
    config: ValidationConfig | None = None,
    data_kind: str = "synthetic",
    dataset_id: str = "",
    dataset_version: str = "",
    snapshot_id: str = "",
    integrity_failed: bool = False,
    integrity: dict[str, str] | None = None,
) -> tuple[BacktestResult, ValidationReport]:
    cfg = config or ValidationConfig()
    strategy = CrossSectionalMomentum(lookback=cfg.lookback, top_n=cfg.top_n)
    firewall = RiskFirewall(RiskLimits(max_name_weight=0.55, max_names=5, max_gross=1.05))
    firewall.register_instruments(instruments)

    bt_cfg = BacktestConfig(
        lookback=cfg.lookback,
        cost_bps=cfg.cost_bps,
        slippage_bps=cfg.slippage_bps,
        seed=cfg.seed,
    )
    result = run_backtest(bars, strategy, firewall, bt_cfg)
    performance = performance_from_backtest(result)
    spec = ResearchBacktestSpec(
        dataset_id=dataset_id,
        dataset_version=dataset_version,
        snapshot_id=snapshot_id,
        strategy_name=strategy.name,
        strategy_version=strategy.version,
        feature_versions={"momentum": strategy.version},
        lookback=cfg.lookback,
        top_n=cfg.top_n,
        cost_bps=cfg.cost_bps,
        slippage_bps=cfg.slippage_bps,
        slippage_model=cfg.slippage_model,
        seed=cfg.seed,
        data_kind=data_kind,
        universe=[str(i.id) for i in instruments],
        label_horizon_sessions=cfg.label_horizon_sessions,
    )

    wf = evaluate_walk_forward(bars, strategy, firewall, cfg)
    robustness = RobustnessReport(
        cost_points=cost_sensitivity(bars, strategy, firewall, cfg.lookback),
        parameter_points=parameter_surface(
            bars, firewall, cfg.lookbacks, top_n=cfg.top_n, cost_bps=cfg.cost_bps
        ),
        regimes=regime_slices(result),
    )
    robustness.fragile_parameter = is_fragile(robustness.parameter_points)

    rets = simple_returns(result.equity_curve)
    stats = evaluate_returns(
        rets, seed=cfg.seed, n_boot=cfg.n_boot, block_size=cfg.block_size, n_perm=cfg.n_perm
    )

    p_values: list[float] = []
    for point in robustness.parameter_points:
        family_strategy = CrossSectionalMomentum(lookback=point.lookback, top_n=cfg.top_n)
        family_result = run_backtest(
            bars,
            family_strategy,
            firewall,
            BacktestConfig(lookback=point.lookback, cost_bps=cfg.cost_bps, seed=cfg.seed),
        )
        p_val = sign_flip_p_value(
            simple_returns(family_result.equity_curve), n_perm=cfg.n_perm, seed=cfg.seed
        )
        if p_val is not None:
            p_values.append(p_val)
    family = evaluate_family(p_values, method=CorrectionMethod.BENJAMINI_HOCHBERG)
    n_periods = int(result.metrics.get("n_periods", 0.0))
    naive = result.metrics.get("sharpe", 0.0)
    periodic_sharpe = naive / DEFAULT_ANNUALIZATION.sqrt_sessions() if n_periods else 0.0
    dsr = deflated_sharpe(
        periodic_sharpe,
        n_trials=max(len(cfg.lookbacks), 1),
        n_periods=n_periods,
        skew=result.metrics.get("skewness", 0.0),
        excess_kurtosis=result.metrics.get("excess_kurtosis", 0.0),
    )
    overfitting = probability_of_backtest_overfitting([], [])

    cost_20 = next((p for p in robustness.cost_points if p.cost_bps == 20.0), None)
    cost_ok = None if cost_20 is None else cost_20.total_return > 0.0

    gate = evaluate_research_gate(
        integrity_failed=integrity_failed,
        next_bar_fill=bt_cfg.fill_policy == "next_bar",
        cost_bps=cfg.cost_bps,
        data_kind=data_kind,
        walk_forward_windows=len(wf.plan.windows),
        oos_sharpe=wf.oos_sharpe,
        cost_still_positive_at_20bps=cost_ok,
        parameter_fragile=robustness.fragile_parameter,
        statistical_status=stats.status,
        n_hypotheses=len(cfg.lookbacks),
        test_used_for_selection=False,
    )

    eq_base = run_backtest(
        bars,
        EqualWeightBaseline(),
        firewall,
        BacktestConfig(lookback=cfg.lookback, cost_bps=cfg.cost_bps, seed=cfg.seed),
    )
    rnd = run_backtest(
        bars,
        RandomSignalBaseline(seed=cfg.seed, top_n=cfg.top_n),
        firewall,
        BacktestConfig(lookback=cfg.lookback, cost_bps=cfg.cost_bps, seed=cfg.seed),
    )
    bench = evaluate_benchmark(
        result.equity_curve, result.dates, CashBenchmark(), result.initial_equity
    )
    decay = signal_decay(bars, _collect_signals(bars, strategy, cfg.lookback))
    env = environment()

    report = ValidationReport(
        config_hash=spec.identity(),
        data_kind=data_kind,
        spec=spec,
        performance=performance,
        walk_forward=wf,
        oos_windows=len(wf.plan.windows),
        oos_sharpe=wf.oos_sharpe,
        oos_total_return=wf.oos_total_return,
        robustness=robustness,
        statistics=stats,
        multiple_testing=family,
        deflated_sharpe=dsr,
        overfitting=overfitting,
        gate=gate,
        benchmark=bench.model_dump(mode="json"),
        attribution=empty_attribution(),
        decay=decay,
        liquidity=evaluate_liquidity(),
        subperiod=subperiod_returns(result.dates, result.equity_curve, bucket="month"),
        baseline_sharpe=eq_base.metrics.get("sharpe"),
        random_baseline_sharpe=rnd.metrics.get("sharpe"),
        seed=cfg.seed,
        git_dirty=git_dirty(),
        python_version=env.get("python", ""),
        integrity=dict(integrity or {}),
    )
    if gate.outcome is GateOutcome.PROMOTED_TO_PAPER and data_kind == "synthetic":
        raise RuntimeError("synthetic results cannot be promoted")
    return result, report


def evaluate_walk_forward(
    bars: dict[InstrumentId, list[OHLCVBar]],
    strategy: CrossSectionalMomentum,
    firewall: RiskFirewall,
    config: ValidationConfig,
) -> WalkForwardEval:
    calendar = shared_calendar(bars)
    plan = generate_walk_forward(
        calendar,
        train_sessions=config.train_sessions,
        test_sessions=config.test_sessions,
        step_sessions=config.step_sessions,
        kind=config.window_kind,
        embargo_sessions=config.embargo_sessions,
        label_horizon_sessions=config.label_horizon_sessions,
    )
    oos_rets: list[float] = []
    window_returns: list[float] = []
    temporally_ok = True
    for window in plan.windows:
        if window.train_end >= window.test_start:
            temporally_ok = False
        if window.purged_train_end is not None and window.purged_train_end >= window.test_start:
            temporally_ok = False
        result = run_backtest(
            bars,
            strategy,
            firewall,
            BacktestConfig(
                lookback=config.lookback,
                cost_bps=config.cost_bps,
                eval_start=window.test_start,
                eval_end=window.test_end,
                seed=config.seed,
            ),
        )
        window_returns.append(result.total_return)
        oos_rets.extend(simple_returns(result.equity_curve))
    oos_sharpe = sharpe(oos_rets) if len(oos_rets) >= 2 else None
    oos_total: float | None
    if oos_rets:
        compounded = 1.0
        for value in oos_rets:
            compounded *= 1.0 + value
        oos_total = compounded - 1.0
    else:
        oos_total = None
    return WalkForwardEval(
        plan=plan,
        oos_sharpe=oos_sharpe,
        oos_total_return=oos_total,
        window_returns=window_returns,
        windows_temporally_ok=temporally_ok,
    )


def _collect_signals(
    bars: dict[InstrumentId, list[OHLCVBar]],
    strategy: CrossSectionalMomentum,
    lookback: int,
) -> dict[datetime, list[Signal]]:
    calendar = shared_calendar(bars)
    out: dict[datetime, list[Signal]] = {}
    if len(calendar) < lookback + 3:
        return out
    for i in range(lookback + 1, len(calendar) - 1):
        as_of = calendar[i]
        states = build_cross_section(bars, as_of, lookback)
        ctx = StrategyContext(as_of=as_of, bars=[], market_states=states)
        out[as_of] = strategy.generate_signals(ctx)
    return out
