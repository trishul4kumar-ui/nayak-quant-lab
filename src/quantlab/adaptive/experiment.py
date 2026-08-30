"""Adaptive research experiments. Adaptation is not alpha and cannot promote itself."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from quantlab import __version__
from quantlab.adaptive.decay import estimate_half_life
from quantlab.adaptive.definition import AdaptiveModelDefinition, LearnerKind
from quantlab.adaptive.engine import run_adaptive
from quantlab.adaptive.prequential import PrequentialResult
from quantlab.adaptive.registry import get_adaptive_model
from quantlab.adaptive.stability import assess_stability
from quantlab.adaptive.state import DecayEstimate, StabilityReport
from quantlab.backtest.spec import config_hash
from quantlab.core.config import LiveSafetyGates
from quantlab.core.identifiers import ExperimentId, InstrumentId
from quantlab.domain.models import ExperimentRun, ExperimentStatus, Instrument, OHLCVBar
from quantlab.domain.research import DataLineage
from quantlab.features.engine import session_calendar
from quantlab.models.registry import ExperimentLedger
from quantlab.research.envinfo import environment, git_commit, git_dirty
from quantlab.research.gate import GateOutcome, ResearchGateResult, evaluate_research_gate
from quantlab.research.integrity import evaluate_integrity


class AdaptiveExperimentReport(BaseModel):
    schema_version: str = "1"
    adaptive_model_id: str
    identity_hash: str
    prequential: PrequentialResult
    decay: DecayEstimate
    stability: StabilityReport
    gate: ResearchGateResult
    integrity: dict[str, str] = Field(default_factory=dict)
    data_kind: str = "synthetic"
    note: str = (
        "Adaptive improvement is not alpha. Synthetic results cannot promote. "
        "Prompt 05 remains the promotion gate."
    )


class AdaptiveComparison(BaseModel):
    schema_version: str = "1"
    rows: list[dict[str, Any]] = Field(default_factory=list)
    family_size: int = 0
    gate_outcome: str = ""
    note: str = (
        "STATIC vs ROLLING vs EXPANDING vs EWMA vs ENSEMBLE. "
        "A higher synthetic IC is not market evidence."
    )


def run_adaptive_experiment(
    *,
    bars: dict[InstrumentId, list[OHLCVBar]],
    instruments: list[Instrument],
    model: AdaptiveModelDefinition,
    data_kind: str = "synthetic",
    dataset_id: str = "",
    dataset_version: str = "",
    snapshot_id: str = "",
    checksum: str = "",
    family_size: int = 1,
    ledger_path: Path | None = None,
    append: bool = False,
    leaked: bool = False,
    update_before_predict: bool = False,
    holdout_contaminated: bool = False,
) -> tuple[AdaptiveExperimentReport, ExperimentRun, PrequentialResult]:
    _panels, _labels, preq = run_adaptive(
        model,
        bars,
        leaky_full_sample=leaked,
        update_before_predict=update_before_predict,
    )
    ics = [p.ic for p in preq.points if p.ic is not None]
    decay = estimate_half_life(ics)
    stability = assess_stability(
        preq.final_state or _empty_state_stub(model, bars),
        preq.weights_path,
    )
    dates = session_calendar(bars)
    used_ml = model.learner in {LearnerKind.BAYESIAN_HIT, LearnerKind.IC_WEIGHTED_ENSEMBLE}
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
        future_normalization=leaked,
        future_regime=leaked and bool(model.regime_model_id),
        hmm_smoothing=False,
        future_parameter_selection=holdout_contaminated,
        test_used_for_selection=holdout_contaminated,
        online_update_order_ok=not update_before_predict,
        future_adaptive_parameter=leaked or holdout_contaminated,
        future_ensemble_performance=leaked and model.learner is LearnerKind.IC_WEIGHTED_ENSEMBLE,
        holdout_contaminated=holdout_contaminated,
        feature_available_time_ok=not leaked,
    )
    gate = evaluate_research_gate(
        integrity_failed=integrity.failed(),
        next_bar_fill=True,
        cost_bps=10.0,
        data_kind=data_kind,
        walk_forward_windows=0,
        oos_sharpe=None,
        cost_still_positive_at_20bps=None,
        parameter_fragile=False,
        statistical_status=preq.status,
        n_hypotheses=family_size,
        test_used_for_selection=holdout_contaminated,
    )
    report = AdaptiveExperimentReport(
        adaptive_model_id=model.adaptive_model_id,
        identity_hash=model.identity_hash(),
        prequential=preq,
        decay=decay,
        stability=stability,
        gate=gate,
        integrity=integrity.as_str_map(),
        data_kind=data_kind,
    )
    run = _ledger_row(
        model, report, instruments, dataset_id, dataset_version, snapshot_id, checksum, family_size
    )
    if append and ledger_path is not None:
        ExperimentLedger(ledger_path).append(run)
        _write_artifacts(ledger_path.parent / "artifacts", run, report, model)
    return report, run, preq


def run_named_adaptive_experiment(
    adaptive_model_id: str,
    *,
    ledger_path: Path,
    n_days: int = 80,
    family_size: int = 1,
    fabric_root: Path | None = None,
    append: bool = True,
) -> tuple[AdaptiveExperimentReport, ExperimentRun, PrequentialResult]:
    from quantlab.research.pipeline import load_synthetic_frame

    frame = load_synthetic_frame(n_days=n_days, ledger_path=ledger_path, fabric_root=fabric_root)
    return run_adaptive_experiment(
        bars=frame.bars,
        instruments=frame.instruments,
        model=get_adaptive_model(adaptive_model_id),
        data_kind=frame.record.data_kind.value,
        dataset_id=frame.record.dataset_id,
        dataset_version=frame.record.version,
        snapshot_id=frame.record.snapshot_id,
        checksum=frame.record.checksum,
        family_size=family_size,
        ledger_path=ledger_path,
        append=append,
    )


def run_adaptive_comparison(
    *,
    bars: dict[InstrumentId, list[OHLCVBar]],
    instruments: list[Instrument],
    model_ids: list[str] | None = None,
    ledger_path: Path | None = None,
    append: bool = False,
    data_kind: str = "synthetic",
) -> AdaptiveComparison:
    ids = model_ids or [
        "static_mom20",
        "rolling_ic_mom20",
        "expanding_ic_mom20",
        "ewma_ic_mom20",
        "ensemble_ic_mom",
    ]
    rows: list[dict[str, Any]] = []
    family = len(ids)
    gate = "warn"
    for model_id in ids:
        report, run, preq = run_adaptive_experiment(
            bars=bars,
            instruments=instruments,
            model=get_adaptive_model(model_id),
            data_kind=data_kind,
            family_size=family,
            ledger_path=ledger_path,
            append=append,
        )
        gate = report.gate.outcome.value
        rows.append(
            {
                "adaptive_model_id": model_id,
                "policy": get_adaptive_model(model_id).policy.value,
                "mean_ic": preq.mean_ic,
                "n_scored": preq.n_scored,
                "coverage": preq.coverage,
                "hit_rate": preq.hit_rate,
                "n_resets": len(preq.resets),
                "gate_outcome": report.gate.outcome.value,
                "experiment_id": run.id,
                "stability_flags": report.stability.flags,
            }
        )
    return AdaptiveComparison(rows=rows, family_size=family, gate_outcome=gate)


def _empty_state_stub(
    model: AdaptiveModelDefinition, bars: dict[InstrumentId, list[OHLCVBar]]
) -> Any:
    from quantlab.adaptive.learners import empty_state

    dates = session_calendar(bars)
    return empty_state(model, dates[0] if dates else datetime(2024, 1, 2, tzinfo=UTC))


def _ledger_row(
    model: AdaptiveModelDefinition,
    report: AdaptiveExperimentReport,
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
        provider="adaptive_research",
        dataset_version=dataset_version,
        ingested_at=datetime.now(tz=UTC),
        transformations=["prequential_predict_update"],
        dataset_id=dataset_id,
        snapshot_id=snapshot_id,
        data_kind=report.data_kind,
        checksum=checksum,
        source="prompt10",
    )
    metrics: dict[str, float] = {
        "n_scored": float(report.prequential.n_scored),
        "n_predictions": float(report.prequential.n_predictions),
    }
    if report.prequential.mean_ic is not None:
        metrics["prequential_ic"] = report.prequential.mean_ic
    if report.prequential.coverage is not None:
        metrics["coverage"] = report.prequential.coverage
    return ExperimentRun(
        id=str(ExperimentId()),
        name=f"adaptive_{model.adaptive_model_id}",
        hypothesis="adaptation is a research process, not automatic alpha",
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
        config_hash=config_hash({"adaptive": model.identity_hash()}),
        research_family_id="adaptive_models",
        n_hypotheses_in_family=family_size,
        selection_stage="adaptive",
        gate_outcome=report.gate.outcome.value,
        gate_reasons=report.gate.as_str_map(),
        git_dirty=git_dirty(),
        python_version=env.get("python", ""),
        validation={"path": "adaptive", "prompt05_suite": "not_run"},
        adaptive_model_id=model.adaptive_model_id,
        adaptive_model_version=model.version,
        adaptation_policy=model.policy.value,
        random_seed=model.seed,
        feature_identity_hash=model.identity_hash(),
        alpha_id=",".join(model.alpha_ids),
        regime_model_id=model.regime_model_id,
    )


def _write_artifacts(
    root: Path,
    run: ExperimentRun,
    report: AdaptiveExperimentReport,
    model: AdaptiveModelDefinition,
) -> None:
    import json

    folder = root / run.id
    folder.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "config": {
            "experiment_id": run.id,
            "config_hash": run.config_hash,
            "adaptive_model_id": model.adaptive_model_id,
            "identity_hash": model.identity_hash(),
            "policy": model.policy.value,
            "data_kind": report.data_kind,
            "seed": run.random_seed,
        },
        "adaptive_definition": model.model_dump(mode="json"),
        "prequential": report.prequential.model_dump(mode="json"),
        "decay": report.decay.model_dump(mode="json"),
        "stability": report.stability.model_dump(mode="json"),
        "integrity": run.integrity,
        "lineage": run.lineage,
        "validation": run.validation,
    }
    for name, body in payload.items():
        (folder / f"{name}.json").write_text(
            json.dumps(body, indent=2, default=str) + "\n", encoding="utf-8"
        )
