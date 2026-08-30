"""Portfolio experiments on the existing next-bar engine. Not a second backtester."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, Field

from quantlab import __version__
from quantlab.alpha.combinations import combine_panels
from quantlab.alpha.definition import get_alpha
from quantlab.alpha.ensemble import (
    AlphaEnsemble,
    apply_panel_sign,
    combine_alpha_panels,
    get_ensemble,
)
from quantlab.alpha.ic import FeatureICReport, information_coefficient
from quantlab.backtest.engine import BacktestConfig, BacktestResult, run_backtest
from quantlab.backtest.spec import config_hash
from quantlab.core.config import LiveSafetyGates
from quantlab.core.errors import (
    AlignmentError,
    CovarianceError,
    InfeasiblePortfolio,
    OptimizationError,
)
from quantlab.core.identifiers import ExperimentId, InstrumentId
from quantlab.domain.models import (
    ExperimentRun,
    ExperimentStatus,
    Instrument,
    OHLCVBar,
    TargetPosition,
)
from quantlab.domain.research import DataLineage
from quantlab.features.correlation import PairCorrelation, correlate_panels
from quantlab.features.definition import NormalizationMethod
from quantlab.features.engine import Panel, compute_panel, session_calendar
from quantlab.features.normalize import apply_cross_section
from quantlab.features.registry import get_feature
from quantlab.labels.definition import forward_return
from quantlab.labels.engine import compute_label_panel
from quantlab.models.registry import ExperimentLedger
from quantlab.portfolio.baselines import targets_to_map
from quantlab.portfolio.builder import construct_targets, is_rebalance
from quantlab.portfolio.contribution import ContributionReport, incremental_ic
from quantlab.portfolio.diagnostics import PortfolioDiagnostics, diagnose
from quantlab.portfolio.spec import MissingAlphaPolicy, PortfolioModel, get_portfolio_model
from quantlab.portfolio.strategy import WeightMapStrategy
from quantlab.research.envinfo import environment, git_commit, git_dirty
from quantlab.research.gate import GateOutcome, ResearchGateResult, evaluate_research_gate
from quantlab.research.integrity import evaluate_integrity
from quantlab.risk.firewall import RiskFirewall, RiskLimits


class PortfolioExperimentReport(BaseModel):
    schema_version: str = "1"
    portfolio_id: str
    ensemble_id: str
    identity_hash: str
    n_rebalances: int = 0
    last_diagnostics: PortfolioDiagnostics | None = None
    ic: FeatureICReport | None = None
    contribution: ContributionReport | None = None
    correlation: list[PairCorrelation] = Field(default_factory=list)
    gate: ResearchGateResult
    integrity: dict[str, str] = Field(default_factory=dict)
    data_kind: str = "synthetic"
    infeasible: bool = False
    note: str = (
        "A rejected or infeasible portfolio is a valid research result. "
        "Synthetic performance is not market evidence. The optimizer does not invent alpha."
    )


def alpha_panel_for(
    alpha_id: str, bars: dict[InstrumentId, list[OHLCVBar]], dates: list[datetime]
) -> Panel:
    alpha = get_alpha(alpha_id)
    feat_panels = [compute_panel(get_feature(fid), bars, dates) for fid in alpha.input_features]
    combined = combine_panels(feat_panels, alpha.transformation)
    return apply_panel_sign(combined, alpha.expected_direction)


def ensemble_score_panel(
    ensemble: AlphaEnsemble,
    bars: dict[InstrumentId, list[OHLCVBar]],
    dates: list[datetime],
) -> tuple[Panel, dict[str, Panel]]:
    components: dict[str, Panel] = {}
    panels: list[Panel] = []
    for item in ensemble.components:
        panel = alpha_panel_for(item.alpha_id, bars, dates)
        components[item.alpha_id] = panel
        panels.append(panel)
    return combine_alpha_panels(ensemble, panels), components


def apply_missing_policy(
    row: dict[str, float],
    universe: list[str],
    policy: MissingAlphaPolicy,
) -> dict[str, float]:
    allowed = set(universe)
    present = {k: v for k, v in row.items() if k in allowed}
    if policy is MissingAlphaPolicy.NEUTRALIZE:
        if len(present) >= 2:
            scaled = apply_cross_section(present, NormalizationMethod.ZSCORE_CS)
        else:
            scaled = dict(present)
        for name in universe:
            scaled.setdefault(name, 0.0)
        return scaled
    return present


def ensemble_correlations(components: dict[str, Panel]) -> list[PairCorrelation]:
    ids = list(components)
    pairs: list[PairCorrelation] = []
    for i, left in enumerate(ids):
        for right in ids[i + 1 :]:
            pairs.append(correlate_panels(left, components[left], right, components[right]))
    return pairs


def build_weight_map(
    model: PortfolioModel,
    scores: Panel,
    bars: dict[InstrumentId, list[OHLCVBar]],
    universe: list[str],
) -> tuple[dict[datetime, list[TargetPosition]], PortfolioDiagnostics | None, bool, int]:
    dates = sorted(scores)
    weights_by_date: dict[datetime, list[TargetPosition]] = {}
    prev: dict[str, float] = {}
    prev_as_of: datetime | None = None
    last_diag: PortfolioDiagnostics | None = None
    infeasible = False
    n_rebalances = 0
    for i, as_of in enumerate(dates):
        if not is_rebalance(model.rebalance.value, as_of, prev_as_of, i):
            held = (
                [t.model_copy() for t in weights_by_date.get(prev_as_of, [])] if prev_as_of else []
            )
            weights_by_date[as_of] = held
            continue
        row = apply_missing_policy(scores[as_of], universe, model.missing_alpha)
        if len(row) < 2:
            weights_by_date[as_of] = []
            prev = {}
            prev_as_of = as_of
            continue
        try:
            proposal, cov, status = construct_targets(
                model, row, as_of, bars=bars, prev_weights=prev
            )
        except InfeasiblePortfolio:
            infeasible = True
            break
        except (CovarianceError, OptimizationError, AlignmentError):
            held = (
                [t.model_copy() for t in weights_by_date.get(prev_as_of, [])] if prev_as_of else []
            )
            weights_by_date[as_of] = held
            prev_as_of = as_of
            continue
        weights_by_date[as_of] = proposal.targets
        mapped = targets_to_map(proposal.targets)
        last_diag = diagnose(
            mapped, prev=prev, cov=cov, constructor=model.constructor.value, optimizer_status=status
        )
        prev = mapped
        prev_as_of = as_of
        n_rebalances += 1
    return weights_by_date, last_diag, infeasible, n_rebalances


def run_portfolio_experiment(
    *,
    bars: dict[InstrumentId, list[OHLCVBar]],
    instruments: list[Instrument],
    model: PortfolioModel,
    ensemble: AlphaEnsemble,
    data_kind: str = "synthetic",
    dataset_id: str = "",
    dataset_version: str = "",
    snapshot_id: str = "",
    checksum: str = "",
    family_size: int = 1,
    ledger_path: Path | None = None,
    append: bool = False,
    run_engine: bool = True,
) -> tuple[PortfolioExperimentReport, ExperimentRun, BacktestResult | None]:
    dates = session_calendar(bars)
    universe = [str(i.id) for i in instruments]
    scores, components = ensemble_score_panel(ensemble, bars, dates)
    weight_map, last_diag, infeasible, n_reb = build_weight_map(model, scores, bars, universe)
    label = compute_label_panel(forward_return(1), bars, dates)
    ic = information_coefficient(scores, label)
    contrib = incremental_ic(
        scores,
        components,
        {item.alpha_id: item.weight for item in ensemble.components},
        label,
    )
    corr = ensemble_correlations(components)
    integrity = evaluate_integrity(
        bars=[bar for series in bars.values() for bar in series],
        states=[],
        as_of_times=dates,
        next_bar_fill=True,
        cost_bps=model.cost_bps,
        slippage_model="none",
        live_trading=LiveSafetyGates().live_trading,
        n_experiments_in_family=family_size,
        used_ml=False,
        data_kind=data_kind,
        pit_query_verified=True,
        future_covariance=False,
        future_ranking_universe=False,
        feature_available_time_ok=True,
        label_used_as_feature=False,
        future_normalization=False,
    )
    result: BacktestResult | None = None
    if run_engine and not infeasible and weight_map:
        firewall = RiskFirewall(
            RiskLimits(
                max_name_weight=1.0,
                max_names=50,
                max_gross=1.05,
                allow_short=not model.long_only,
            )
        )
        firewall.register_instruments(instruments)
        strategy = WeightMapStrategy(weight_map)
        result = run_backtest(
            bars,
            strategy,
            firewall,
            BacktestConfig(lookback=20, cost_bps=model.cost_bps),
        )
        result.integrity = integrity.as_str_map()
    gate = evaluate_research_gate(
        integrity_failed=integrity.failed(),
        next_bar_fill=True,
        cost_bps=model.cost_bps,
        data_kind=data_kind,
        walk_forward_windows=0,
        oos_sharpe=None,
        cost_still_positive_at_20bps=None,
        parameter_fragile=False,
        statistical_status=ic.status,
        n_hypotheses=family_size,
        test_used_for_selection=False,
    )
    report = PortfolioExperimentReport(
        portfolio_id=model.portfolio_id,
        ensemble_id=ensemble.ensemble_id,
        identity_hash=model.identity_hash(),
        n_rebalances=n_reb if result is None else result.n_rebalances,
        last_diagnostics=last_diag,
        ic=ic,
        contribution=contrib,
        correlation=corr,
        gate=gate,
        integrity=integrity.as_str_map(),
        data_kind=data_kind,
        infeasible=infeasible,
    )
    run = _ledger_row(
        model,
        ensemble,
        report,
        instruments,
        dataset_id,
        dataset_version,
        snapshot_id,
        checksum,
        result,
    )
    if append and ledger_path is not None:
        ExperimentLedger(ledger_path).append(run)
        _write_artifacts(ledger_path.parent / "artifacts", run, report, ensemble, model)
    return report, run, result


def run_named_portfolio_experiment(
    portfolio_id: str,
    *,
    ledger_path: Path,
    n_days: int = 80,
    family_size: int = 1,
    fabric_root: Path | None = None,
    append: bool = True,
) -> tuple[PortfolioExperimentReport, ExperimentRun, BacktestResult | None]:
    return run_model_on_synthetic(
        get_portfolio_model(portfolio_id),
        ledger_path=ledger_path,
        n_days=n_days,
        family_size=family_size,
        fabric_root=fabric_root,
        append=append,
    )


def run_model_on_synthetic(
    model: PortfolioModel,
    *,
    ledger_path: Path,
    n_days: int = 80,
    family_size: int = 1,
    fabric_root: Path | None = None,
    append: bool = True,
) -> tuple[PortfolioExperimentReport, ExperimentRun, BacktestResult | None]:
    from quantlab.research.pipeline import load_synthetic_frame

    frame = load_synthetic_frame(n_days=n_days, ledger_path=ledger_path, fabric_root=fabric_root)
    ensemble = get_ensemble(model.ensemble_id)
    return run_portfolio_experiment(
        bars=frame.bars,
        instruments=frame.instruments,
        model=model,
        ensemble=ensemble,
        data_kind=frame.record.data_kind.value,
        dataset_id=frame.record.dataset_id,
        dataset_version=frame.record.version,
        snapshot_id=frame.record.snapshot_id,
        checksum=frame.record.checksum,
        family_size=family_size,
        ledger_path=ledger_path,
        append=append,
    )


def run_named_ensemble_experiment(
    ensemble_id: str,
    *,
    ledger_path: Path,
    n_days: int = 80,
    fabric_root: Path | None = None,
    append: bool = False,
) -> tuple[Panel, FeatureICReport, list[PairCorrelation]]:
    from quantlab.research.pipeline import load_synthetic_frame

    frame = load_synthetic_frame(n_days=n_days, ledger_path=ledger_path, fabric_root=fabric_root)
    ensemble = get_ensemble(ensemble_id)
    dates = session_calendar(frame.bars)
    scores, components = ensemble_score_panel(ensemble, frame.bars, dates)
    label = compute_label_panel(forward_return(1), frame.bars, dates)
    return scores, information_coefficient(scores, label), ensemble_correlations(components)


def _ledger_row(
    model: PortfolioModel,
    ensemble: AlphaEnsemble,
    report: PortfolioExperimentReport,
    instruments: list[Instrument],
    dataset_id: str,
    dataset_version: str,
    snapshot_id: str,
    checksum: str,
    result: BacktestResult | None,
) -> ExperimentRun:
    env = environment()
    status = (
        ExperimentStatus.FAILED
        if report.gate.outcome is GateOutcome.REJECT
        else ExperimentStatus.PASSED
    )
    if report.infeasible:
        status = ExperimentStatus.FAILED
    lineage = DataLineage(
        provider="portfolio_construction",
        dataset_version=dataset_version,
        ingested_at=datetime.now(tz=UTC),
        transformations=["ensemble", "constructor", "constraints", "next_bar_backtest"],
        dataset_id=dataset_id,
        snapshot_id=snapshot_id,
        data_kind=report.data_kind,
        checksum=checksum,
        source="prompt07",
    )
    metrics = dict(result.metrics) if result is not None else {}
    if report.ic is not None and report.ic.spearman_mean is not None:
        metrics["spearman_ic"] = report.ic.spearman_mean
        metrics["ic_n"] = float(report.ic.n)
    if report.last_diagnostics is not None:
        metrics["gross"] = report.last_diagnostics.gross
        metrics["net"] = report.last_diagnostics.net
        metrics["turnover"] = report.last_diagnostics.turnover
        if report.last_diagnostics.estimated_volatility is not None:
            metrics["estimated_volatility"] = report.last_diagnostics.estimated_volatility
        if report.last_diagnostics.concentration_hhi is not None:
            metrics["hhi"] = report.last_diagnostics.concentration_hhi
    return ExperimentRun(
        id=str(ExperimentId()),
        name=f"portfolio_{model.portfolio_id}",
        hypothesis=f"ensemble {ensemble.ensemble_id} via {model.constructor.value}",
        status=status,
        git_commit=git_commit(),
        dataset_version=dataset_version or "unspecified",
        universe=[str(i.id) for i in instruments],
        transaction_cost_bps=model.cost_bps,
        dataset_id=dataset_id,
        snapshot_id=snapshot_id,
        data_kind=report.data_kind,
        lineage=lineage.as_dict(),
        metrics=metrics,
        integrity=report.integrity,
        application_version=__version__,
        conclusion=report.note,
        config_hash=config_hash(
            {"portfolio": model.identity_hash(), "ensemble": ensemble.identity_hash()}
        ),
        research_family_id=model.family_id,
        n_hypotheses_in_family=1,
        selection_stage="portfolio_construction",
        gate_outcome=report.gate.outcome.value,
        gate_reasons=report.gate.as_str_map(),
        git_dirty=git_dirty(),
        python_version=env.get("python", ""),
        validation={"path": "portfolio", "prompt05_suite": "not_run"},
        portfolio_id=model.portfolio_id,
        portfolio_version=model.version,
        ensemble_id=ensemble.ensemble_id,
        optimizer=model.constructor.value,
        feature_identity_hash=model.identity_hash(),
        hypothesis_id=ensemble.hypothesis_id,
    )


def _write_artifacts(
    root: Path,
    run: ExperimentRun,
    report: PortfolioExperimentReport,
    ensemble: AlphaEnsemble,
    model: PortfolioModel,
) -> None:
    import json

    folder = root / run.id
    folder.mkdir(parents=True, exist_ok=True)
    payload = {
        "config": {"experiment_id": run.id, "config_hash": run.config_hash},
        "ensemble": ensemble.model_dump(mode="json"),
        "constraints": [c.model_dump(mode="json") for c in model.constraints],
        "risk": None
        if report.last_diagnostics is None
        else report.last_diagnostics.model_dump(mode="json"),
        "integrity": run.integrity,
        "lineage": run.lineage,
        "validation": run.validation,
        "contribution": None
        if report.contribution is None
        else report.contribution.model_dump(mode="json"),
        "correlation": [p.model_dump(mode="json") for p in report.correlation],
    }
    for name, body in payload.items():
        (folder / f"{name}.json").write_text(
            json.dumps(body, indent=2, default=str) + "\n", encoding="utf-8"
        )
