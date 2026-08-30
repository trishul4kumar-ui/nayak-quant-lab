"""Regime research experiments. A regime label is not alpha and not a forecast."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from quantlab import __version__
from quantlab.backtest.spec import config_hash
from quantlab.core.config import LiveSafetyGates
from quantlab.core.identifiers import ExperimentId, InstrumentId
from quantlab.domain.models import ExperimentRun, ExperimentStatus, Instrument, OHLCVBar
from quantlab.domain.research import DataLineage
from quantlab.factors.engine import compute_factor_panel
from quantlab.factors.registry import get_factor
from quantlab.features.engine import session_calendar
from quantlab.labels.definition import forward_return
from quantlab.labels.engine import compute_label_panel
from quantlab.models.registry import ExperimentLedger
from quantlab.regimes.condition import ConditionalSlice, conditional_covariance, conditional_ic
from quantlab.regimes.definition import RegimeModel
from quantlab.regimes.detectors import RegimeObservation
from quantlab.regimes.duration import DurationReport, durations
from quantlab.regimes.engine import classify, compute_state_panel
from quantlab.regimes.registry import get_regime_model
from quantlab.regimes.snapshot import StateSnapshot
from quantlab.regimes.temporal import TemporalReport, summarize_temporal
from quantlab.regimes.transitions import TransitionMatrix, transition_matrix
from quantlab.research.envinfo import environment, git_commit, git_dirty
from quantlab.research.gate import GateOutcome, ResearchGateResult, evaluate_research_gate
from quantlab.research.integrity import evaluate_integrity


class RegimeExperimentReport(BaseModel):
    schema_version: str = "1"
    regime_model_id: str
    identity_hash: str
    n_snapshots: int = 0
    n_labelled: int = 0
    transitions: TransitionMatrix
    durations: DurationReport
    temporal: TemporalReport
    conditional_ic: list[ConditionalSlice] = Field(default_factory=list)
    conditional_cov: list[ConditionalSlice] = Field(default_factory=list)
    gate: ResearchGateResult
    integrity: dict[str, str] = Field(default_factory=dict)
    data_kind: str = "synthetic"
    note: str = (
        "A regime label is not a forecast and not alpha. "
        "Synthetic regime detection is not evidence of tradable market regimes. "
        "Prompt 05 remains the promotion gate."
    )


def run_regime_experiment(
    *,
    bars: dict[InstrumentId, list[OHLCVBar]],
    instruments: list[Instrument],
    model: RegimeModel,
    data_kind: str = "synthetic",
    dataset_id: str = "",
    dataset_version: str = "",
    snapshot_id: str = "",
    checksum: str = "",
    family_size: int = 1,
    ledger_path: Path | None = None,
    append: bool = False,
    predictive: bool = True,
    leaked: bool = False,
    hmm_smoothing: bool = False,
    full_sample_fit: bool = False,
) -> tuple[RegimeExperimentReport, ExperimentRun, list[StateSnapshot], list[RegimeObservation]]:
    snapshots = compute_state_panel(bars, lookback=model.lookback)
    observations = classify(model, snapshots, predictive=predictive)
    trans = transition_matrix(observations)
    dur = durations(observations)
    temporal = summarize_temporal(snapshots)
    dates = session_calendar(bars)
    factor_panel, _obs = compute_factor_panel(get_factor("style_momentum_20"), bars, dates)
    fwd = compute_label_panel(forward_return(1), bars, dates)
    labels = sorted({row.hard_label for row in observations if row.hard_label is not None})
    cond_ic = [conditional_ic(factor_panel, fwd, observations, lab) for lab in labels]
    names = [str(i.id) for i in instruments]
    cond_cov = [conditional_covariance(bars, observations, lab, names) for lab in labels]
    integrity = evaluate_integrity(
        bars=[bar for series in bars.values() for bar in series],
        states=[],
        as_of_times=dates,
        next_bar_fill=True,
        cost_bps=10.0,
        slippage_model="none",
        live_trading=LiveSafetyGates().live_trading,
        n_experiments_in_family=family_size,
        used_ml=model.detector.value.startswith("hmm") or "cluster" in model.detector.value,
        data_kind=data_kind,
        pit_query_verified=True,
        future_normalization=leaked,
        future_regime=leaked,
        hmm_smoothing=hmm_smoothing,
        full_sample_regime_fit=full_sample_fit,
        feature_available_time_ok=not leaked,
    )
    from quantlab.domain.research import CheckResult

    gate = evaluate_research_gate(
        integrity_failed=integrity.failed(),
        next_bar_fill=True,
        cost_bps=10.0,
        data_kind=data_kind,
        walk_forward_windows=0,
        oos_sharpe=None,
        cost_still_positive_at_20bps=None,
        parameter_fragile=False,
        statistical_status=CheckResult.NOT_TESTED,
        n_hypotheses=family_size,
        test_used_for_selection=False,
    )
    labelled = sum(1 for row in observations if row.hard_label is not None)
    report = RegimeExperimentReport(
        regime_model_id=model.regime_model_id,
        identity_hash=model.identity_hash(),
        n_snapshots=len(snapshots),
        n_labelled=labelled,
        transitions=trans,
        durations=dur,
        temporal=temporal,
        conditional_ic=cond_ic,
        conditional_cov=cond_cov,
        gate=gate,
        integrity=integrity.as_str_map(),
        data_kind=data_kind,
    )
    run = _ledger_row(
        model, report, instruments, dataset_id, dataset_version, snapshot_id, checksum, family_size
    )
    if append and ledger_path is not None:
        ExperimentLedger(ledger_path).append(run)
        _write_artifacts(ledger_path.parent / "artifacts", run, report, model, observations)
    return report, run, snapshots, observations


def run_named_regime_experiment(
    regime_model_id: str,
    *,
    ledger_path: Path,
    n_days: int = 80,
    family_size: int = 1,
    fabric_root: Path | None = None,
    append: bool = True,
    predictive: bool = True,
) -> tuple[RegimeExperimentReport, ExperimentRun, list[StateSnapshot], list[RegimeObservation]]:
    from quantlab.research.pipeline import load_synthetic_frame

    frame = load_synthetic_frame(n_days=n_days, ledger_path=ledger_path, fabric_root=fabric_root)
    return run_regime_experiment(
        bars=frame.bars,
        instruments=frame.instruments,
        model=get_regime_model(regime_model_id),
        data_kind=frame.record.data_kind.value,
        dataset_id=frame.record.dataset_id,
        dataset_version=frame.record.version,
        snapshot_id=frame.record.snapshot_id,
        checksum=frame.record.checksum,
        family_size=family_size,
        ledger_path=ledger_path,
        append=append,
        predictive=predictive,
    )


def _ledger_row(
    model: RegimeModel,
    report: RegimeExperimentReport,
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
        provider="regime_research",
        dataset_version=dataset_version,
        ingested_at=datetime.now(tz=UTC),
        transformations=["state_snapshot", "regime_classify"],
        dataset_id=dataset_id,
        snapshot_id=snapshot_id,
        data_kind=report.data_kind,
        checksum=checksum,
        source="prompt09",
    )
    metrics: dict[str, float] = {
        "n_snapshots": float(report.n_snapshots),
        "n_labelled": float(report.n_labelled),
        "n_transitions": float(report.transitions.n_transitions),
    }
    return ExperimentRun(
        id=str(ExperimentId()),
        name=f"regime_{model.regime_model_id}",
        hypothesis="regime is a description of observable state, not alpha",
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
        config_hash=config_hash({"regime": model.identity_hash()}),
        research_family_id="regime_models",
        n_hypotheses_in_family=family_size,
        selection_stage="regime",
        gate_outcome=report.gate.outcome.value,
        gate_reasons=report.gate.as_str_map(),
        git_dirty=git_dirty(),
        python_version=env.get("python", ""),
        validation={"path": "regime", "prompt05_suite": "not_run"},
        regime_model_id=model.regime_model_id,
        regime_model_version=model.version,
        random_seed=int(model.parameters.get("seed", 0)),
        feature_identity_hash=model.identity_hash(),
    )


def _write_artifacts(
    root: Path,
    run: ExperimentRun,
    report: RegimeExperimentReport,
    model: RegimeModel,
    observations: list[RegimeObservation],
) -> None:
    import json

    folder = root / run.id
    folder.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "config": {
            "experiment_id": run.id,
            "config_hash": run.config_hash,
            "regime_model_id": model.regime_model_id,
            "identity_hash": model.identity_hash(),
            "data_kind": report.data_kind,
            "seed": run.random_seed,
        },
        "regime_definition": model.model_dump(mode="json"),
        "timeline": [row.model_dump(mode="json") for row in observations],
        "transitions": report.transitions.model_dump(mode="json"),
        "durations": report.durations.model_dump(mode="json"),
        "temporal": report.temporal.model_dump(mode="json"),
        "conditional_ic": [row.model_dump(mode="json") for row in report.conditional_ic],
        "integrity": run.integrity,
        "lineage": run.lineage,
        "validation": run.validation,
    }
    for name, body in payload.items():
        (folder / f"{name}.json").write_text(
            json.dumps(body, indent=2, default=str) + "\n", encoding="utf-8"
        )
