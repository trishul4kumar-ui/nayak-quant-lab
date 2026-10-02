"""TCA ledger rows."""

from __future__ import annotations

from pathlib import Path

from quantlab import __version__
from quantlab.domain.models import ExperimentRun, ExperimentStatus
from quantlab.models.registry import ExperimentLedger
from quantlab.research.envinfo import environment, git_commit, git_dirty
from quantlab.tca.models import TCARequest, TCAResult
from quantlab.tca.repository import persist
from quantlab.tca.service import run_tca


def _run_row(result: TCAResult) -> ExperimentRun:
    return ExperimentRun(
        id=result.run.tca_run_id,
        name=f"tca:{result.kind.value}",
        hypothesis="Implementation shortfall is measurement, not a live fill.",
        status=ExperimentStatus.PASSED,
        git_commit=git_commit(),
        dataset_version=result.run.oms_run_id,
        universe=[],
        feature_versions={"kind": result.kind.value},
        label_definition="not_applicable",
        transaction_cost_bps=10.0,
        snapshot_id=result.run.oms_run_id,
        data_kind="synthetic",
        metrics={
            "shortfall": result.shortfall.total or 0.0,
            "capacity_breaches": float(sum(1 for row in result.capacity.scenarios if row.breach)),
        },
        application_version=__version__,
        conclusion="tca observation; not broker TCA",
        config_hash=result.run.tca_hash,
        selection_stage="tca",
        git_dirty=git_dirty(),
        python_version=environment().get("python", ""),
        research_type="tca",
        oms_run_id=result.run.oms_run_id,
        tca_run_id=result.run.tca_run_id,
        tca_hash=result.run.tca_hash,
        execution_model_id=result.calibration.model_id if result.calibration else "",
        calibration_hash=result.run.calibration_hash,
        arrival_price_policy=result.run.arrival_policy.value,
        shortfall=result.shortfall.total or 0.0,
        cost_decomposition=result.kind.value,
        capacity_policy_id=result.capacity.policy_id,
        capacity_result_id=result.run.tca_run_id,
        fragility_status=result.fragility.status.value,
    )


def run_tca_experiment(
    request: TCARequest | None = None,
    *,
    ledger_path: Path,
    append: bool = True,
) -> tuple[TCAResult, ExperimentRun]:
    result = run_tca(request)
    persist()
    row = _run_row(result)
    if append:
        ExperimentLedger(ledger_path).append(row)
    return result, row
