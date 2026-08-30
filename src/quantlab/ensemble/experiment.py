"""Ensemble experiments. An ensemble is not a portfolio and cannot promote itself."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from quantlab import __version__
from quantlab.adaptive.decay import estimate_half_life
from quantlab.adaptive.engine import run_adaptive
from quantlab.adaptive.registry import get_adaptive_model
from quantlab.adaptive.state import DecayEstimate
from quantlab.backtest.spec import config_hash
from quantlab.core.config import LiveSafetyGates
from quantlab.core.identifiers import ExperimentId, InstrumentId
from quantlab.domain.models import ExperimentRun, ExperimentStatus, Instrument, OHLCVBar
from quantlab.domain.research import DataLineage
from quantlab.ensemble.definition import EnsembleDefinition, EnsembleLeakFlags
from quantlab.ensemble.diversity import (
    AttributionReport,
    DiversityReport,
    LeaveOneOutReport,
    WeightStabilityReport,
    assess_weight_stability,
    attribution,
    leave_one_out,
    pairwise_correlations,
)
from quantlab.ensemble.engine import EnsembleResult, run_ensemble
from quantlab.ensemble.registry import get_ensemble
from quantlab.features.engine import Panel, session_calendar
from quantlab.models.registry import ExperimentLedger
from quantlab.research.envinfo import environment, git_commit, git_dirty
from quantlab.research.gate import GateOutcome, ResearchGateResult, evaluate_research_gate
from quantlab.research.integrity import evaluate_integrity


class EnsembleExperimentReport(BaseModel):
    schema_version: str = "1"
    ensemble_id: str
    identity_hash: str
    combination_method: str
    weighting_policy: str
    walkforward: EnsembleResult
    decay: DecayEstimate
    diversity: DiversityReport
    leave_one_out: LeaveOneOutReport
    attribution: AttributionReport
    stability: WeightStabilityReport
    gate: ResearchGateResult
    integrity: dict[str, str] = Field(default_factory=dict)
    data_kind: str = "synthetic"
    n_candidates: int = 1
    search_truncated: bool = False
    note: str = (
        "An ensemble is not a portfolio. Incremental information vs best component "
        "and equal-weight is required. Synthetic results cannot promote. "
        "Prompt 05 remains the promotion gate."
    )


class EnsembleComparison(BaseModel):
    schema_version: str = "1"
    rows: list[dict[str, Any]] = Field(default_factory=list)
    family_size: int = 0
    gate_outcome: str = ""
    search_truncated: bool = False
    note: str = (
        "Best component vs equal vs static vs corr vs dynamic vs meta vs stack. "
        "A higher synthetic IC is not market evidence."
    )


def run_ensemble_experiment(
    *,
    bars: dict[InstrumentId, list[OHLCVBar]],
    instruments: list[Instrument],
    definition: EnsembleDefinition,
    data_kind: str = "synthetic",
    dataset_id: str = "",
    dataset_version: str = "",
    snapshot_id: str = "",
    checksum: str = "",
    family_size: int = 1,
    ledger_path: Path | None = None,
    append: bool = False,
    leaks: EnsembleLeakFlags | None = None,
    overrides: dict[str, Panel] | None = None,
    holdout_start: datetime | None = None,
    search_truncated: bool = False,
) -> tuple[EnsembleExperimentReport, ExperimentRun, EnsembleResult]:
    flags = leaks or EnsembleLeakFlags()
    dates = session_calendar(bars)
    panels, labels, result = run_ensemble(
        definition,
        bars,
        leaks=flags,
        snapshot_id=snapshot_id,
        overrides=overrides,
        holdout_start=holdout_start,
    )
    names = definition.component_ids()
    ics = [p.ic for p in result.points if p.ic is not None]
    decay = estimate_half_life(ics)
    diversity = pairwise_correlations(panels, dates, names)
    loo = leave_one_out(panels, labels, dates, names)
    attr = attribution(
        panels, labels, dates, names, result.predictions, result.weights_path, diversity
    )
    stability = assess_weight_stability(result.weights_path)
    used_ml = definition.weighting_policy.value.endswith("stack") or definition.is_meta_alpha
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
        future_normalization=flags.future_normalization,
        future_regime=flags.future_regime,
        hmm_smoothing=False,
        future_parameter_selection=flags.holdout_contaminated or flags.future_hyperparameter,
        test_used_for_selection=flags.holdout_contaminated,
        holdout_contaminated=flags.holdout_contaminated,
        feature_available_time_ok=not flags.future_meta_feature,
        future_covariance=flags.future_covariance or flags.future_correlation,
        future_hyperparameter=flags.future_hyperparameter,
        future_calibration=False,
        model_state_mutation=False,
        future_component_performance=flags.future_component_performance,
        future_ensemble_weight=flags.future_weights or flags.full_sample_replay,
        future_correlation=flags.future_correlation,
        future_meta_feature=flags.future_meta_feature,
        future_component_selection=flags.future_component_selection,
        future_stacking_prediction=flags.stacking_leak or flags.future_stacking,
        future_pruning=flags.future_pruning,
        stacking_leak=flags.stacking_leak,
        full_sample_ensemble_replay=flags.full_sample_replay,
        future_ensemble_performance=flags.future_weights,
    )
    gate = evaluate_research_gate(
        integrity_failed=integrity.failed(),
        next_bar_fill=True,
        cost_bps=10.0,
        data_kind=data_kind,
        walk_forward_windows=result.n_scored,
        oos_sharpe=None,
        cost_still_positive_at_20bps=None,
        parameter_fragile=False,
        statistical_status=result.status,
        n_hypotheses=family_size,
        test_used_for_selection=flags.holdout_contaminated,
    )
    report = EnsembleExperimentReport(
        ensemble_id=definition.ensemble_id,
        identity_hash=definition.identity_hash(),
        combination_method=definition.combination_method.value,
        weighting_policy=definition.weighting_policy.value,
        walkforward=result,
        decay=decay,
        diversity=diversity,
        leave_one_out=loo,
        attribution=attr,
        stability=stability,
        gate=gate,
        integrity=integrity.as_str_map(),
        data_kind=data_kind,
        n_candidates=family_size,
        search_truncated=search_truncated,
    )
    run = _ledger_row(
        definition,
        report,
        instruments,
        dataset_id,
        dataset_version,
        snapshot_id,
        checksum,
        family_size,
    )
    if append and ledger_path is not None:
        ExperimentLedger(ledger_path).append(run)
        _write_artifacts(ledger_path.parent / "artifacts", run, report, definition)
    return report, run, result


def run_named_ensemble_experiment(
    ensemble_id: str,
    *,
    ledger_path: Path,
    n_days: int = 80,
    family_size: int = 1,
    fabric_root: Path | None = None,
    append: bool = True,
    leaks: EnsembleLeakFlags | None = None,
) -> tuple[EnsembleExperimentReport, ExperimentRun, EnsembleResult]:
    from quantlab.research.pipeline import load_synthetic_frame

    frame = load_synthetic_frame(n_days=n_days, ledger_path=ledger_path, fabric_root=fabric_root)
    return run_ensemble_experiment(
        bars=frame.bars,
        instruments=frame.instruments,
        definition=get_ensemble(ensemble_id),
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


def run_ensemble_comparison(
    *,
    bars: dict[InstrumentId, list[OHLCVBar]],
    instruments: list[Instrument],
    ensemble_ids: list[str] | None = None,
    ledger_path: Path | None = None,
    append: bool = False,
    data_kind: str = "synthetic",
    max_trials: int | None = None,
) -> EnsembleComparison:
    ids = ensemble_ids or [
        "ew_mom_5_20",
        "static_ic_mom",
        "corr_mom",
        "roll_ic_mom",
        "ridge_stack_mom",
        "meta_ols_mom",
    ]
    truncated = False
    used = list(ids)
    if max_trials is not None and len(used) > max_trials:
        used = used[:max_trials]
        truncated = True
    rows: list[dict[str, Any]] = []
    family = len(ids)
    gate = "warn"
    for ensemble_id in used:
        report, run, wf = run_ensemble_experiment(
            bars=bars,
            instruments=instruments,
            definition=get_ensemble(ensemble_id),
            data_kind=data_kind,
            family_size=family,
            ledger_path=ledger_path,
            append=append,
            search_truncated=truncated,
        )
        gate = report.gate.outcome.value
        rows.append(
            {
                "ensemble_id": ensemble_id,
                "weighting_policy": get_ensemble(ensemble_id).weighting_policy.value,
                "mean_ic": wf.mean_ic,
                "equal_weight_ic": wf.equal_weight_ic,
                "best_component_id": wf.best_component_id,
                "best_component_ic": wf.best_component_ic,
                "n_scored": wf.n_scored,
                "hit_rate": wf.hit_rate,
                "gate_outcome": report.gate.outcome.value,
                "experiment_id": run.id,
                "redundancy": report.diversity.redundancy,
            }
        )
    return EnsembleComparison(
        rows=rows, family_size=family, gate_outcome=gate, search_truncated=truncated
    )


def compare_static_vs_adaptive(
    *,
    bars: dict[InstrumentId, list[OHLCVBar]],
    instruments: list[Instrument],
) -> dict[str, Any]:
    report, _run, wf = run_ensemble_experiment(
        bars=bars,
        instruments=instruments,
        definition=get_ensemble("ew_mom_5_20"),
        append=False,
    )
    _p, _l, preq = run_adaptive(get_adaptive_model("ensemble_ic_mom"), bars)
    return {
        "static_ensemble_id": "ew_mom_5_20",
        "static_ic": wf.mean_ic,
        "adaptive_model_id": "ensemble_ic_mom",
        "adaptive_ic": preq.mean_ic,
        "gate_outcome": report.gate.outcome.value,
        "note": "Prompt 10 adaptive ensemble is not reimplemented. Synthetic IC is not alpha.",
    }


def _ledger_row(
    definition: EnsembleDefinition,
    report: EnsembleExperimentReport,
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
        provider="ensemble_research",
        dataset_version=dataset_version,
        ingested_at=datetime.now(tz=UTC),
        transformations=["pit_combine_predict_realize"],
        dataset_id=dataset_id,
        snapshot_id=snapshot_id,
        data_kind=report.data_kind,
        checksum=checksum,
        source="prompt12",
    )
    metrics: dict[str, float] = {
        "n_scored": float(report.walkforward.n_scored),
        "n_predictions": float(report.walkforward.n_predictions),
        "n_candidates": float(family_size),
        "cost_bps": 10.0,
    }
    if report.walkforward.mean_ic is not None:
        metrics["oos_ic"] = report.walkforward.mean_ic
    if report.walkforward.equal_weight_ic is not None:
        metrics["equal_weight_ic"] = report.walkforward.equal_weight_ic
    if report.walkforward.best_component_ic is not None:
        metrics["best_component_ic"] = report.walkforward.best_component_ic
    return ExperimentRun(
        id=str(ExperimentId()),
        name=f"ensemble_{definition.ensemble_id}",
        hypothesis="combining sources is a research question, not automatic alpha",
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
        config_hash=config_hash({"ensemble": definition.identity_hash()}),
        research_family_id="combination_ensembles",
        n_hypotheses_in_family=family_size,
        selection_stage="meta_ensemble",
        gate_outcome=report.gate.outcome.value,
        gate_reasons=report.gate.as_str_map(),
        git_dirty=git_dirty(),
        python_version=env.get("python", ""),
        validation={"path": "ensemble", "prompt05_suite": "not_run"},
        ensemble_id=definition.ensemble_id,
        combination_method=definition.combination_method.value,
        weighting_policy=definition.weighting_policy.value,
        meta_alpha_id=definition.meta_alpha_id,
        component_ids=",".join(definition.component_ids()),
        candidate_count=family_size,
        random_seed=definition.seed,
        feature_identity_hash=definition.identity_hash(),
        regime_model_id=definition.regime_model_id,
    )


def _write_artifacts(
    root: Path,
    run: ExperimentRun,
    report: EnsembleExperimentReport,
    definition: EnsembleDefinition,
) -> None:
    import json

    folder = root / run.id
    folder.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "config": {
            "experiment_id": run.id,
            "config_hash": run.config_hash,
            "ensemble_id": definition.ensemble_id,
            "identity_hash": definition.identity_hash(),
            "weighting_policy": definition.weighting_policy.value,
            "data_kind": report.data_kind,
            "seed": run.random_seed,
            "n_candidates": report.n_candidates,
            "search_truncated": report.search_truncated,
        },
        "ensemble_definition": definition.model_dump(mode="json"),
        "walkforward": report.walkforward.model_dump(mode="json"),
        "diversity": report.diversity.model_dump(mode="json"),
        "leave_one_out": report.leave_one_out.model_dump(mode="json"),
        "attribution": report.attribution.model_dump(mode="json"),
        "stability": report.stability.model_dump(mode="json"),
        "integrity": run.integrity,
        "lineage": run.lineage,
        "validation": run.validation,
    }
    for name, body in payload.items():
        (folder / f"{name}.json").write_text(
            json.dumps(body, indent=2, default=str) + "\n", encoding="utf-8"
        )
