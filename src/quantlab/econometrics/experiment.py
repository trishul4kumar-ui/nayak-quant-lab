"""Econometric ledger rows."""

from __future__ import annotations

from pathlib import Path

from quantlab import __version__
from quantlab.domain.models import ExperimentRun, ExperimentStatus
from quantlab.econometrics.models import EconometricRequest, EconometricResult
from quantlab.econometrics.repository import persist
from quantlab.econometrics.service import run_econometrics
from quantlab.models.registry import ExperimentLedger
from quantlab.research.envinfo import environment, git_commit, git_dirty


def _run_row(result: EconometricResult) -> ExperimentRun:
    return ExperimentRun(
        id=result.run.econometrics_run_id,
        name=f"econometrics:{result.spec.estimator.value}",
        hypothesis="Observed relationships are not automatically causal or economic.",
        status=ExperimentStatus.PASSED,
        git_commit=git_commit(),
        dataset_version=result.spec.snapshot_id,
        universe=list(result.spec.series_ids),
        feature_versions={"estimator": result.spec.estimator.value},
        label_definition="not_applicable",
        transaction_cost_bps=10.0,
        snapshot_id=result.spec.snapshot_id,
        data_kind="synthetic",
        metrics={
            "tested_count": float(result.run.tested_count),
        },
        application_version=__version__,
        conclusion="econometric observation; not a claim",
        config_hash=result.run.run_hash,
        selection_stage="econometrics",
        git_dirty=git_dirty(),
        python_version=environment().get("python", ""),
        research_type="econometrics",
        econometrics_run_id=result.run.econometrics_run_id,
        econometrics_hash=result.run.run_hash,
        econometric_spec_id=result.spec.spec_id,
    )


def run_econometrics_experiment(
    request: EconometricRequest | None = None,
    *,
    ledger_path: Path,
    append: bool = True,
) -> tuple[EconometricResult, ExperimentRun]:
    result = run_econometrics(request)
    persist()
    row = _run_row(result)
    if append:
        ExperimentLedger(ledger_path).append(row)
    return result, row
