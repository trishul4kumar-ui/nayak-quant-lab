"""Feature/alpha experiment pipeline. Does not replace Prompt 05 validation."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, Field

from quantlab import __version__
from quantlab.alpha.artifacts import write_feature_artifacts
from quantlab.alpha.combinations import combine_panels
from quantlab.alpha.decay import PredictiveDecayReport, predictive_decay
from quantlab.alpha.definition import AlphaDefinition, get_alpha
from quantlab.alpha.ic import FeatureICReport, information_coefficient
from quantlab.alpha.quantiles import QuantileReport, quantile_analysis
from quantlab.backtest.spec import config_hash
from quantlab.core.config import LiveSafetyGates
from quantlab.core.identifiers import ExperimentId, HypothesisId, InstrumentId
from quantlab.domain.models import ExperimentRun, ExperimentStatus, Instrument, OHLCVBar
from quantlab.domain.research import DataLineage, ResearchHypothesis, ResearchStatus
from quantlab.features.correlation import PairCorrelation, correlate_panels
from quantlab.features.definition import FeatureDefinition
from quantlab.features.engine import Panel, compute_panel, session_calendar
from quantlab.features.quality import FeatureQualityReport, summarize_quality
from quantlab.features.registry import get_feature
from quantlab.labels.definition import LabelDefinition, forward_return
from quantlab.labels.engine import compute_label_panel
from quantlab.models.registry import ExperimentLedger
from quantlab.research.envinfo import environment, git_commit, git_dirty
from quantlab.research.gate import GateOutcome, ResearchGateResult, evaluate_research_gate
from quantlab.research.integrity import evaluate_integrity


class AlphaExperimentConfig(BaseModel):
    hypothesis: str = "feature predicts next-session return"
    dataset_id: str = ""
    dataset_version: str = ""
    snapshot_id: str = ""
    checksum: str = ""
    universe: list[str] = Field(default_factory=list)
    feature_id: str
    label_id: str = "forward_return_1"
    horizons: list[int] = Field(default_factory=lambda: [1, 2, 5, 10, 20])
    normalization: str = "none"
    train_test_protocol: str = "ic_full_sample_diagnostic"
    cost_bps: float = 10.0
    seed: int = 0
    validation_protocol: str = "next_bar_cost_adjusted"
    family_id: str = ""
    n_hypotheses_in_family: int = 1
    selection_stage: str = "feature_ic"
    data_kind: str = "synthetic"
    min_ic_sample: int = 8
    source: str = "memory_or_fabric"


class FeatureExperimentReport(BaseModel):
    schema_version: str = "1"
    feature_id: str
    feature_version: str
    identity_hash: str
    n_aligned: int = 0
    quality: FeatureQualityReport
    ic: FeatureICReport
    quantiles: QuantileReport
    decay: PredictiveDecayReport
    correlation: PairCorrelation | None = None
    gate: ResearchGateResult
    integrity: dict[str, str] = Field(default_factory=dict)
    data_kind: str = "synthetic"
    note: str = (
        "A weak or null IC is a valid research result. "
        "Synthetic IC is not market evidence. Prompt 05 remains the promotion gate."
    )


def panels_almost_equal(left: Panel, right: Panel, tol: float = 1e-12) -> bool:
    dates = set(left) & set(right)
    if not dates:
        return False
    matched = 0
    total = 0
    for as_of in dates:
        for key, value in left[as_of].items():
            if key not in right[as_of]:
                continue
            total += 1
            if abs(value - right[as_of][key]) <= tol:
                matched += 1
    return total > 0 and matched == total


def run_feature_experiment(
    *,
    bars: dict[InstrumentId, list[OHLCVBar]],
    instruments: list[Instrument],
    feature: FeatureDefinition,
    label: LabelDefinition,
    config: AlphaExperimentConfig,
    ledger_path: Path | None = None,
    artifacts_dir: Path | None = None,
    append: bool = False,
    compare_feature: FeatureDefinition | None = None,
) -> tuple[FeatureExperimentReport, ExperimentRun]:
    dates = session_calendar(bars)
    feature_panel = compute_panel(feature, bars, dates)
    label_panel = compute_label_panel(label, bars, dates)
    leak = panels_almost_equal(feature_panel, label_panel)
    quality = summarize_quality(feature_panel, expected_names=len(instruments))
    ic = information_coefficient(feature_panel, label_panel, min_sample=config.min_ic_sample)
    quantiles = quantile_analysis(feature_panel, label_panel)
    decay = predictive_decay(
        feature_panel,
        bars,
        horizons=tuple(config.horizons),
        min_sample=config.min_ic_sample,
    )
    corr: PairCorrelation | None = None
    if compare_feature is not None:
        other = compute_panel(compare_feature, bars, dates)
        corr = correlate_panels(
            feature.feature_id, feature_panel, compare_feature.feature_id, other
        )
    integrity = evaluate_integrity(
        bars=[bar for series in bars.values() for bar in series],
        states=[],
        as_of_times=dates,
        next_bar_fill=True,
        cost_bps=config.cost_bps,
        slippage_model="none",
        live_trading=LiveSafetyGates().live_trading,
        n_experiments_in_family=config.n_hypotheses_in_family,
        used_ml=False,
        data_kind=config.data_kind,
        pit_query_verified=True,
        label_used_as_feature=leak,
        future_normalization=False,
        future_ranking_universe=False,
        feature_available_time_ok=True,
    )
    gate = evaluate_research_gate(
        integrity_failed=integrity.failed(),
        next_bar_fill=True,
        cost_bps=config.cost_bps,
        data_kind=config.data_kind,
        walk_forward_windows=0,
        oos_sharpe=None,
        cost_still_positive_at_20bps=None,
        parameter_fragile=False,
        statistical_status=ic.status,
        n_hypotheses=config.n_hypotheses_in_family,
        test_used_for_selection=False,
    )
    report = FeatureExperimentReport(
        feature_id=feature.feature_id,
        feature_version=feature.version,
        identity_hash=feature.identity_hash(),
        n_aligned=ic.n,
        quality=quality,
        ic=ic,
        quantiles=quantiles,
        decay=decay,
        correlation=corr,
        gate=gate,
        integrity=integrity.as_str_map(),
        data_kind=config.data_kind,
    )
    run = _experiment_run(feature, label, config, instruments, report, integrity.as_str_map(), gate)
    if append and ledger_path is not None:
        ExperimentLedger(ledger_path).append(run)
        dest = artifacts_dir or (ledger_path.parent / "artifacts")
        write_feature_artifacts(
            dest,
            run,
            extra={
                "feature_definition": feature.model_dump(mode="json"),
                "label_definition": label.model_dump(mode="json"),
                "quality": quality.model_dump(mode="json"),
                "ic": ic.model_dump(mode="json"),
                "quantiles": quantiles.model_dump(mode="json"),
                "decay": decay.model_dump(mode="json"),
                "correlations": None if corr is None else corr.model_dump(mode="json"),
            },
        )
    return report, run


def run_alpha_experiment(
    *,
    bars: dict[InstrumentId, list[OHLCVBar]],
    instruments: list[Instrument],
    alpha: AlphaDefinition,
    config: AlphaExperimentConfig,
    ledger_path: Path | None = None,
    artifacts_dir: Path | None = None,
    append: bool = False,
) -> tuple[FeatureExperimentReport, ExperimentRun]:
    dates = session_calendar(bars)
    panels = [compute_panel(get_feature(fid), bars, dates) for fid in alpha.input_features]
    combined = combine_panels(panels, alpha.transformation)
    label = forward_return(alpha.horizon)
    synthetic_feature = FeatureDefinition(
        feature_id=alpha.alpha_id,
        version=alpha.version,
        name=alpha.name,
        mathematical_definition=alpha.mathematical_definition,
        inputs=alpha.input_features,
        lookback=max(get_feature(fid).lookback for fid in alpha.input_features),
        operator=get_feature(alpha.input_features[0]).operator,
        family=get_feature(alpha.input_features[0]).family,
        family_id=alpha.family_id,
        notes="alpha combination panel; operator copied from first input for identity only",
    )
    label_panel = compute_label_panel(label, bars, dates)
    quality = summarize_quality(combined, expected_names=len(instruments))
    ic = information_coefficient(combined, label_panel, min_sample=config.min_ic_sample)
    quantiles = quantile_analysis(
        combined, label_panel, expected_direction=alpha.expected_direction
    )
    decay = predictive_decay(combined, bars, horizons=tuple(config.horizons))
    integrity = evaluate_integrity(
        bars=[bar for series in bars.values() for bar in series],
        states=[],
        as_of_times=dates,
        next_bar_fill=True,
        cost_bps=config.cost_bps,
        slippage_model="none",
        live_trading=LiveSafetyGates().live_trading,
        n_experiments_in_family=config.n_hypotheses_in_family,
        used_ml=False,
        data_kind=config.data_kind,
        pit_query_verified=True,
        label_used_as_feature=False,
        future_normalization=False,
        future_ranking_universe=False,
        feature_available_time_ok=True,
    )
    gate = evaluate_research_gate(
        integrity_failed=integrity.failed(),
        next_bar_fill=True,
        cost_bps=config.cost_bps,
        data_kind=config.data_kind,
        walk_forward_windows=0,
        oos_sharpe=None,
        cost_still_positive_at_20bps=None,
        parameter_fragile=False,
        statistical_status=ic.status,
        n_hypotheses=config.n_hypotheses_in_family,
        test_used_for_selection=False,
    )
    report = FeatureExperimentReport(
        feature_id=alpha.alpha_id,
        feature_version=alpha.version,
        identity_hash=synthetic_feature.identity_hash(),
        n_aligned=ic.n,
        quality=quality,
        ic=ic,
        quantiles=quantiles,
        decay=decay,
        gate=gate,
        integrity=integrity.as_str_map(),
        data_kind=config.data_kind,
    )
    run = _experiment_run(
        synthetic_feature,
        label,
        config,
        instruments,
        report,
        integrity.as_str_map(),
        gate,
        alpha_id=alpha.alpha_id,
    )
    if append and ledger_path is not None:
        ExperimentLedger(ledger_path).append(run)
        dest = artifacts_dir or (ledger_path.parent / "artifacts")
        write_feature_artifacts(
            dest,
            run,
            extra={
                "feature_definition": alpha.model_dump(mode="json"),
                "label_definition": label.model_dump(mode="json"),
                "quality": quality.model_dump(mode="json"),
                "ic": ic.model_dump(mode="json"),
                "quantiles": quantiles.model_dump(mode="json"),
                "decay": decay.model_dump(mode="json"),
            },
        )
    return report, run


def run_named_feature_experiment(
    feature_id: str,
    *,
    ledger_path: Path,
    n_days: int = 80,
    horizon: int = 1,
    family_size: int = 1,
    fabric_root: Path | None = None,
    append: bool = True,
) -> tuple[FeatureExperimentReport, ExperimentRun]:
    from quantlab.research.pipeline import load_synthetic_frame

    frame = load_synthetic_frame(n_days=n_days, ledger_path=ledger_path, fabric_root=fabric_root)
    feature = get_feature(feature_id)
    label = forward_return(horizon)
    compare = None if feature_id == "momentum_20" else get_feature("momentum_20")
    config = AlphaExperimentConfig(
        hypothesis=f"{feature_id} predicts forward_return_{horizon}",
        dataset_id=frame.record.dataset_id,
        dataset_version=frame.record.version,
        snapshot_id=frame.record.snapshot_id,
        checksum=frame.record.checksum,
        universe=[str(i.id) for i in frame.instruments],
        feature_id=feature_id,
        label_id=label.label_id,
        family_id=feature.family_id,
        n_hypotheses_in_family=family_size,
        data_kind=frame.record.data_kind.value,
        source="data_fabric",
    )
    return run_feature_experiment(
        bars=frame.bars,
        instruments=frame.instruments,
        feature=feature,
        label=label,
        config=config,
        ledger_path=ledger_path,
        artifacts_dir=ledger_path.parent / "artifacts",
        append=append,
        compare_feature=compare,
    )


def run_named_alpha_experiment(
    alpha_id: str,
    *,
    ledger_path: Path,
    n_days: int = 80,
    family_size: int = 1,
    fabric_root: Path | None = None,
    append: bool = True,
) -> tuple[FeatureExperimentReport, ExperimentRun]:
    from quantlab.research.pipeline import load_synthetic_frame

    frame = load_synthetic_frame(n_days=n_days, ledger_path=ledger_path, fabric_root=fabric_root)
    alpha = get_alpha(alpha_id)
    config = AlphaExperimentConfig(
        hypothesis=alpha.mathematical_definition,
        dataset_id=frame.record.dataset_id,
        dataset_version=frame.record.version,
        snapshot_id=frame.record.snapshot_id,
        checksum=frame.record.checksum,
        universe=[str(i.id) for i in frame.instruments],
        feature_id=alpha_id,
        label_id=f"forward_return_{alpha.horizon}",
        family_id=alpha.family_id,
        n_hypotheses_in_family=family_size,
        data_kind=frame.record.data_kind.value,
        source="data_fabric",
        selection_stage="alpha_ic",
    )
    return run_alpha_experiment(
        bars=frame.bars,
        instruments=frame.instruments,
        alpha=alpha,
        config=config,
        ledger_path=ledger_path,
        artifacts_dir=ledger_path.parent / "artifacts",
        append=append,
    )


def _experiment_run(
    feature: FeatureDefinition,
    label: LabelDefinition,
    config: AlphaExperimentConfig,
    instruments: list[Instrument],
    report: FeatureExperimentReport,
    integrity: dict[str, str],
    gate: ResearchGateResult,
    alpha_id: str = "",
) -> ExperimentRun:
    env = environment()
    hypothesis = ResearchHypothesis(
        id=str(HypothesisId()),
        title=config.hypothesis,
        statement=config.hypothesis,
        expected_direction=feature.family.value,
        expected_horizon=str(label.horizon),
        pre_registered=False,
        universe=[str(i.id) for i in instruments] or config.universe,
        status=ResearchStatus.EXPERIMENTAL,
    )
    status = (
        ExperimentStatus.FAILED if gate.outcome is GateOutcome.REJECT else ExperimentStatus.PASSED
    )
    lineage = DataLineage(
        provider=config.source,
        dataset_version=config.dataset_version,
        ingested_at=datetime.now(tz=UTC),
        transformations=["feature_engine", "label_engine", "ic", "quantiles", "decay"],
        feature_versions={feature.feature_id: feature.version},
        signal_version=feature.implementation_version,
        dataset_id=config.dataset_id,
        snapshot_id=config.snapshot_id,
        data_kind=config.data_kind,
        checksum=config.checksum,
        source=config.source,
    )
    spec = {
        "feature_id": feature.feature_id,
        "feature_version": feature.version,
        "identity": feature.identity_hash(),
        "label": label.label_id,
        "snapshot_id": config.snapshot_id,
        "horizons": config.horizons,
        "cost_bps": config.cost_bps,
        "seed": config.seed,
    }
    metrics: dict[str, float] = {
        "ic_n": float(report.ic.n),
        "quality_n": float(report.quality.n),
    }
    if report.ic.spearman_mean is not None:
        metrics["spearman_ic"] = report.ic.spearman_mean
    if report.quantiles.long_short_spread is not None:
        metrics["quantile_spread"] = report.quantiles.long_short_spread
    return ExperimentRun(
        id=str(ExperimentId()),
        name=f"feature_{feature.feature_id}",
        hypothesis=config.hypothesis,
        status=status,
        git_commit=git_commit(),
        dataset_version=config.dataset_version or "unspecified",
        universe=hypothesis.universe,
        feature_versions={feature.feature_id: feature.version},
        label_definition=label.label_id,
        hyperparameters={
            "lookback": feature.lookback,
            "horizon": label.horizon,
            "cost_bps": config.cost_bps,
            "n_hypotheses_in_family": config.n_hypotheses_in_family,
        },
        test_period=config.train_test_protocol,
        transaction_cost_bps=config.cost_bps,
        random_seed=config.seed,
        hypothesis_id=hypothesis.id,
        alpha_id=alpha_id,
        dataset_id=config.dataset_id,
        snapshot_id=config.snapshot_id,
        data_kind=config.data_kind,
        lineage=lineage.as_dict(),
        metrics=metrics,
        integrity=integrity,
        application_version=__version__,
        conclusion=report.note,
        config_hash=config_hash(spec),
        research_family_id=config.family_id or feature.family_id,
        n_hypotheses_in_family=config.n_hypotheses_in_family,
        selection_stage=config.selection_stage,
        gate_outcome=gate.outcome.value,
        gate_reasons=gate.as_str_map(),
        validation_protocol=config.validation_protocol,
        git_dirty=git_dirty(),
        python_version=env.get("python", ""),
        validation={"path": "feature_ic", "prompt05_suite": "not_run"},
        feature_id=feature.feature_id,
        feature_version=feature.version,
        label_id=label.label_id,
        feature_identity_hash=feature.identity_hash(),
    )
