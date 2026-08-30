"""Factor research experiments. Factor IC is not a promotion score."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from quantlab import __version__
from quantlab.alpha.ic import FeatureICReport, information_coefficient
from quantlab.backtest.spec import config_hash
from quantlab.core.config import LiveSafetyGates
from quantlab.core.identifiers import ExperimentId, InstrumentId
from quantlab.domain.models import ExperimentRun, ExperimentStatus, Instrument, OHLCVBar
from quantlab.domain.research import DataLineage
from quantlab.factors.definition import FactorDefinition
from quantlab.factors.engine import FactorObservation, compute_factor_panel
from quantlab.factors.registry import get_factor
from quantlab.features.correlation import PairCorrelation, correlate_panels
from quantlab.features.engine import Panel, session_calendar
from quantlab.features.quality import FeatureQualityReport, summarize_quality
from quantlab.labels.definition import forward_return
from quantlab.labels.engine import compute_label_panel
from quantlab.models.registry import ExperimentLedger
from quantlab.research.envinfo import environment, git_commit, git_dirty
from quantlab.research.gate import GateOutcome, ResearchGateResult, evaluate_research_gate
from quantlab.research.integrity import evaluate_integrity


class FactorExperimentReport(BaseModel):
    schema_version: str = "1"
    factor_id: str
    factor_version: str
    identity_hash: str
    observation: FactorObservation
    quality: FeatureQualityReport
    ic: FeatureICReport
    gate: ResearchGateResult
    integrity: dict[str, str] = Field(default_factory=dict)
    data_kind: str = "synthetic"
    note: str = (
        "Factor exposure is not automatic alpha. "
        "Synthetic IC is not market evidence. Prompt 05 remains the promotion gate."
    )


def run_factor_experiment(
    *,
    bars: dict[InstrumentId, list[OHLCVBar]],
    instruments: list[Instrument],
    definition: FactorDefinition,
    data_kind: str = "synthetic",
    dataset_id: str = "",
    dataset_version: str = "",
    snapshot_id: str = "",
    checksum: str = "",
    family_size: int = 1,
    ledger_path: Path | None = None,
    append: bool = False,
    leaked_label: bool = False,
) -> tuple[FactorExperimentReport, ExperimentRun, Panel]:
    dates = session_calendar(bars)
    panel, observation = compute_factor_panel(definition, bars, dates)
    label = compute_label_panel(forward_return(1), bars, dates)
    ic = information_coefficient(panel, label)
    quality = summarize_quality(panel, expected_names=len(instruments))
    integrity = evaluate_integrity(
        bars=[bar for series in bars.values() for bar in series],
        states=[],
        as_of_times=dates,
        next_bar_fill=True,
        cost_bps=10.0,
        slippage_model="none",
        live_trading=LiveSafetyGates().live_trading,
        n_experiments_in_family=family_size,
        used_ml=False,
        data_kind=data_kind,
        pit_query_verified=True,
        future_factor=leaked_label,
        future_beta=leaked_label,
        label_used_as_feature=leaked_label,
        feature_available_time_ok=not leaked_label,
        future_ranking_universe=False,
        future_normalization=False,
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
        statistical_status=ic.status,
        n_hypotheses=family_size,
        test_used_for_selection=False,
    )
    report = FactorExperimentReport(
        factor_id=definition.factor_id,
        factor_version=definition.version,
        identity_hash=definition.identity_hash(),
        observation=observation,
        quality=quality,
        ic=ic,
        gate=gate,
        integrity=integrity.as_str_map(),
        data_kind=data_kind,
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
    return report, run, panel


def run_named_factor_experiment(
    factor_id: str,
    *,
    ledger_path: Path,
    n_days: int = 80,
    family_size: int = 1,
    fabric_root: Path | None = None,
    append: bool = True,
) -> tuple[FactorExperimentReport, ExperimentRun, Panel]:
    from quantlab.research.pipeline import load_synthetic_frame

    frame = load_synthetic_frame(n_days=n_days, ledger_path=ledger_path, fabric_root=fabric_root)
    return run_factor_experiment(
        bars=frame.bars,
        instruments=frame.instruments,
        definition=get_factor(factor_id),
        data_kind=frame.record.data_kind.value,
        dataset_id=frame.record.dataset_id,
        dataset_version=frame.record.version,
        snapshot_id=frame.record.snapshot_id,
        checksum=frame.record.checksum,
        family_size=family_size,
        ledger_path=ledger_path,
        append=append,
    )


def factor_pair_correlation(
    factor_a: str,
    factor_b: str,
    bars: dict[InstrumentId, list[OHLCVBar]],
) -> PairCorrelation:
    dates = session_calendar(bars)
    left, _ = compute_factor_panel(get_factor(factor_a), bars, dates)
    right, _ = compute_factor_panel(get_factor(factor_b), bars, dates)
    return correlate_panels(factor_a, left, factor_b, right)


def _ledger_row(
    definition: FactorDefinition,
    report: FactorExperimentReport,
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
        provider="factor_research",
        dataset_version=dataset_version,
        ingested_at=datetime.now(tz=UTC),
        transformations=["factor_engine", "ic"],
        dataset_id=dataset_id,
        snapshot_id=snapshot_id,
        data_kind=report.data_kind,
        checksum=checksum,
        source="prompt08",
    )
    metrics: dict[str, float] = {}
    if report.ic.spearman_mean is not None:
        metrics["spearman_ic"] = report.ic.spearman_mean
        metrics["ic_n"] = float(report.ic.n)
    return ExperimentRun(
        id=str(ExperimentId()),
        name=f"factor_{definition.factor_id}",
        hypothesis="factor is a systematic exposure, not automatic alpha",
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
        config_hash=config_hash({"factor": definition.identity_hash()}),
        research_family_id=definition.family_id,
        n_hypotheses_in_family=family_size,
        selection_stage="factor_ic",
        gate_outcome=report.gate.outcome.value,
        gate_reasons=report.gate.as_str_map(),
        git_dirty=git_dirty(),
        python_version=env.get("python", ""),
        validation={"path": "factor", "prompt05_suite": "not_run"},
        factor_id=definition.factor_id,
        factor_set=definition.factor_id,
        factor_versions={definition.factor_id: definition.version},
        feature_identity_hash=definition.identity_hash(),
    )


def _write_artifacts(
    root: Path,
    run: ExperimentRun,
    report: FactorExperimentReport,
    definition: FactorDefinition,
) -> None:
    import json

    folder = root / run.id
    folder.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "config": {
            "experiment_id": run.id,
            "config_hash": run.config_hash,
            "factor_id": definition.factor_id,
            "factor_version": definition.version,
            "identity_hash": definition.identity_hash(),
            "data_kind": report.data_kind,
        },
        "factor_definition": definition.model_dump(mode="json"),
        "observation": report.observation.model_dump(mode="json"),
        "quality": report.quality.model_dump(mode="json"),
        "ic": report.ic.model_dump(mode="json"),
        "integrity": run.integrity,
        "lineage": run.lineage,
        "validation": run.validation,
    }
    for name, body in payload.items():
        (folder / f"{name}.json").write_text(
            json.dumps(body, indent=2, default=str) + "\n", encoding="utf-8"
        )
