"""Statistical-model experiments. A model is not alpha and cannot promote itself."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from quantlab import __version__
from quantlab.adaptive.decay import estimate_half_life
from quantlab.adaptive.state import DecayEstimate
from quantlab.backtest.spec import config_hash
from quantlab.core.config import LiveSafetyGates
from quantlab.core.identifiers import ExperimentId, InstrumentId
from quantlab.domain.models import ExperimentRun, ExperimentStatus, Instrument, OHLCVBar
from quantlab.domain.research import DataLineage
from quantlab.features.engine import session_calendar
from quantlab.learning.definition import Algorithm, ModelDefinition
from quantlab.learning.diagnostics import (
    ImportanceReport,
    IncrementalReport,
    ResidualReport,
    StabilityReport,
    coefficient_stability,
    incremental_ic,
    linear_importance,
    residual_report,
)
from quantlab.learning.engine import run_learning
from quantlab.learning.registry import get_model
from quantlab.learning.walkforward import LeakFlags, WalkForwardResult
from quantlab.models.registry import ExperimentLedger
from quantlab.research.envinfo import environment, git_commit, git_dirty
from quantlab.research.gate import GateOutcome, ResearchGateResult, evaluate_research_gate
from quantlab.research.integrity import evaluate_integrity


class ModelExperimentReport(BaseModel):
    schema_version: str = "1"
    model_id: str
    identity_hash: str
    walkforward: WalkForwardResult
    decay: DecayEstimate
    residuals: ResidualReport
    importance: ImportanceReport
    stability: StabilityReport
    incremental: IncrementalReport | None = None
    gate: ResearchGateResult
    integrity: dict[str, str] = Field(default_factory=dict)
    data_kind: str = "synthetic"
    n_candidates: int = 1
    note: str = (
        "A model is not alpha. Incremental information is required. "
        "Synthetic results cannot promote. Prompt 05 remains the promotion gate."
    )


class ModelComparison(BaseModel):
    schema_version: str = "1"
    rows: list[dict[str, Any]] = Field(default_factory=list)
    family_size: int = 0
    gate_outcome: str = ""
    note: str = (
        "NO-SIGNAL vs ALPHA vs OLS vs RIDGE vs TREE. A higher synthetic IC is not market evidence."
    )


def run_model_experiment(
    *,
    bars: dict[InstrumentId, list[OHLCVBar]],
    instruments: list[Instrument],
    model: ModelDefinition,
    data_kind: str = "synthetic",
    dataset_id: str = "",
    dataset_version: str = "",
    snapshot_id: str = "",
    checksum: str = "",
    family_size: int = 1,
    ledger_path: Path | None = None,
    append: bool = False,
    leaks: LeakFlags | None = None,
    baseline_id: str = "alpha_mom20",
) -> tuple[ModelExperimentReport, ExperimentRun, WalkForwardResult]:
    flags = leaks or LeakFlags()
    dataset, predictions, wf, _regimes = run_learning(
        model, bars, leaks=flags, snapshot_id=snapshot_id
    )
    ics = [p.ic for p in wf.points if p.ic is not None]
    decay = estimate_half_life(ics)
    oos_p: list[float] = []
    oos_y: list[float] = []
    for as_of, scores in predictions.items():
        lab = dataset.labels.get(as_of, {})
        for inst, value in scores.items():
            if inst in lab:
                oos_p.append(value)
                oos_y.append(lab[inst])
    residuals = residual_report(oos_p, oos_y)
    importance = (
        linear_importance(wf.final_state) if wf.final_state else ImportanceReport(method="none")
    )
    stability = coefficient_stability([wf.final_state] if wf.final_state else [])
    incremental = None
    if model.model_id != baseline_id:
        _bset, base_pred, _bwf, _r = run_learning(get_model(baseline_id), bars)
        incremental = incremental_ic(base_pred, predictions, dataset.labels)
    dates = session_calendar(bars)
    used_ml = model.algorithm in {
        Algorithm.RANDOM_FOREST,
        Algorithm.GRADIENT_BOOSTING,
        Algorithm.PCA_OLS,
        Algorithm.SELECT_OLS,
        Algorithm.LASSO,
        Algorithm.ELASTIC_NET,
        Algorithm.RIDGE,
        Algorithm.HUBER,
        Algorithm.OLS,
    }
    integrity = evaluate_integrity(
        bars=[bar for series in bars.values() for bar in series],
        states=[],
        as_of_times=dates,
        next_bar_fill=True,
        cost_bps=10.0,
        slippage_model="none",
        live_trading=LiveSafetyGates().live_trading,
        n_experiments_in_family=family_size,
        used_ml=used_ml,
        data_kind=data_kind,
        pit_query_verified=True,
        future_normalization=flags.future_scaler,
        future_regime=False,
        hmm_smoothing=False,
        future_parameter_selection=flags.holdout_contaminated or flags.future_hyperparameter,
        test_used_for_selection=flags.holdout_contaminated,
        label_used_as_feature=flags.label_as_feature,
        holdout_contaminated=flags.holdout_contaminated,
        feature_available_time_ok=not flags.label_as_feature,
        future_model_training=flags.replay_full_sample,
        future_pca=flags.future_pca,
        future_feature_selection=flags.future_selection,
        future_hyperparameter=flags.future_hyperparameter,
        future_calibration=False,
        cross_section_future_leak=flags.replay_full_sample,
        model_replay_leak=flags.replay_full_sample or flags.future_scaler or flags.future_pca,
        model_state_mutation=False,
    )
    gate = evaluate_research_gate(
        integrity_failed=integrity.failed(),
        next_bar_fill=True,
        cost_bps=10.0,
        data_kind=data_kind,
        walk_forward_windows=wf.n_scored,
        oos_sharpe=None,
        cost_still_positive_at_20bps=None,
        parameter_fragile=False,
        statistical_status=wf.status,
        n_hypotheses=family_size,
        test_used_for_selection=flags.holdout_contaminated,
    )
    report = ModelExperimentReport(
        model_id=model.model_id,
        identity_hash=model.identity_hash(),
        walkforward=wf,
        decay=decay,
        residuals=residuals,
        importance=importance,
        stability=stability,
        incremental=incremental,
        gate=gate,
        integrity=integrity.as_str_map(),
        data_kind=data_kind,
        n_candidates=family_size,
    )
    run = _ledger_row(
        model, report, instruments, dataset_id, dataset_version, snapshot_id, checksum, family_size
    )
    if append and ledger_path is not None:
        ExperimentLedger(ledger_path).append(run)
        _write_artifacts(ledger_path.parent / "artifacts", run, report, model)
    return report, run, wf


def run_named_model_experiment(
    model_id: str,
    *,
    ledger_path: Path,
    n_days: int = 80,
    family_size: int = 1,
    fabric_root: Path | None = None,
    append: bool = True,
    leaks: LeakFlags | None = None,
) -> tuple[ModelExperimentReport, ExperimentRun, WalkForwardResult]:
    from quantlab.research.pipeline import load_synthetic_frame

    frame = load_synthetic_frame(n_days=n_days, ledger_path=ledger_path, fabric_root=fabric_root)
    return run_model_experiment(
        bars=frame.bars,
        instruments=frame.instruments,
        model=get_model(model_id),
        data_kind=frame.record.data_kind.value,
        dataset_id=frame.record.dataset_id,
        dataset_version=frame.record.version,
        snapshot_id=frame.record.snapshot_id,
        checksum=frame.record.checksum,
        family_size=family_size,
        ledger_path=ledger_path,
        append=append,
        leaks=leaks,
    )


def run_model_comparison(
    *,
    bars: dict[InstrumentId, list[OHLCVBar]],
    instruments: list[Instrument],
    model_ids: list[str] | None = None,
    ledger_path: Path | None = None,
    append: bool = False,
    data_kind: str = "synthetic",
) -> ModelComparison:
    ids = model_ids or [
        "no_signal",
        "alpha_mom20",
        "ols_mom",
        "ridge_mom",
        "rf_mom",
    ]
    rows: list[dict[str, Any]] = []
    family = len(ids)
    gate = "warn"
    for model_id in ids:
        report, run, wf = run_model_experiment(
            bars=bars,
            instruments=instruments,
            model=get_model(model_id),
            data_kind=data_kind,
            family_size=family,
            ledger_path=ledger_path,
            append=append,
        )
        gate = report.gate.outcome.value
        rows.append(
            {
                "model_id": model_id,
                "algorithm": get_model(model_id).algorithm.value,
                "mean_ic": wf.mean_ic,
                "n_scored": wf.n_scored,
                "oos_rmse": wf.oos_rmse,
                "train_rmse": wf.train_rmse,
                "coverage": wf.coverage,
                "gate_outcome": report.gate.outcome.value,
                "experiment_id": run.id,
                "delta_ic": None if report.incremental is None else report.incremental.delta_ic,
            }
        )
    return ModelComparison(rows=rows, family_size=family, gate_outcome=gate)


def _ledger_row(
    model: ModelDefinition,
    report: ModelExperimentReport,
    instruments: list[Instrument],
    dataset_id: str,
    dataset_version: str,
    snapshot_id: str,
    checksum: str,
    family_size: int,
) -> ExperimentRun:
    env = environment()
    status = (
        ExperimentStatus.FAILED
        if report.gate.outcome is GateOutcome.REJECT
        else ExperimentStatus.PASSED
    )
    lineage = DataLineage(
        provider="statistical_learning",
        dataset_version=dataset_version,
        ingested_at=datetime.now(tz=UTC),
        transformations=["walkforward_predict_then_realize"],
        dataset_id=dataset_id,
        snapshot_id=snapshot_id,
        data_kind=report.data_kind,
        checksum=checksum,
        source="prompt11",
    )
    metrics: dict[str, float] = {
        "n_scored": float(report.walkforward.n_scored),
        "n_predictions": float(report.walkforward.n_predictions),
        "n_candidates": float(family_size),
    }
    if report.walkforward.mean_ic is not None:
        metrics["oos_ic"] = report.walkforward.mean_ic
    if report.walkforward.oos_rmse is not None:
        metrics["oos_rmse"] = report.walkforward.oos_rmse
    return ExperimentRun(
        id=str(ExperimentId()),
        name=f"model_{model.model_id}",
        hypothesis="a statistical model is a research object, not automatic alpha",
        status=status,
        git_commit=git_commit(),
        dataset_version=dataset_version or "unspecified",
        universe=[str(i.id) for i in instruments],
        transaction_cost_bps=10.0,
        dataset_id=dataset_id,
        snapshot_id=snapshot_id,
        data_kind=report.data_kind,
        lineage=lineage.as_dict(),
        metrics=metrics,
        integrity=report.integrity,
        application_version=__version__,
        conclusion=report.note,
        config_hash=config_hash({"model": model.identity_hash()}),
        research_family_id="statistical_models",
        n_hypotheses_in_family=family_size,
        selection_stage="model",
        gate_outcome=report.gate.outcome.value,
        gate_reasons=report.gate.as_str_map(),
        git_dirty=git_dirty(),
        python_version=env.get("python", ""),
        validation={"path": "learning", "prompt05_suite": "not_run"},
        statistical_model_id=model.model_id,
        statistical_model_version=model.version,
        algorithm=model.algorithm.value,
        random_seed=model.random_seed,
        feature_identity_hash=model.identity_hash(),
        label_id=model.target,
        regime_model_id=model.regime_model_id,
    )


def _write_artifacts(
    root: Path,
    run: ExperimentRun,
    report: ModelExperimentReport,
    model: ModelDefinition,
) -> None:
    import json

    folder = root / run.id
    folder.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "config": {
            "experiment_id": run.id,
            "config_hash": run.config_hash,
            "model_id": model.model_id,
            "identity_hash": model.identity_hash(),
            "algorithm": model.algorithm.value,
            "data_kind": report.data_kind,
            "seed": run.random_seed,
            "n_candidates": report.n_candidates,
        },
        "model_definition": model.model_dump(mode="json"),
        "walkforward": report.walkforward.model_dump(mode="json"),
        "decay": report.decay.model_dump(mode="json"),
        "residuals": report.residuals.model_dump(mode="json"),
        "importance": report.importance.model_dump(mode="json"),
        "integrity": run.integrity,
        "lineage": run.lineage,
        "validation": run.validation,
    }
    for name, body in payload.items():
        (folder / f"{name}.json").write_text(
            json.dumps(body, indent=2, default=str) + "\n", encoding="utf-8"
        )
