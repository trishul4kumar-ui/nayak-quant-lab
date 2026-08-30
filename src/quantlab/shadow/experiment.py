"""Shadow ledger rows. Reuses JSONL ExperimentLedger. Not a second ledger."""

from __future__ import annotations

from contextlib import suppress
from pathlib import Path

from quantlab import __version__
from quantlab.domain.models import ExperimentRun, ExperimentStatus
from quantlab.knowledge.errors import KnowledgeError
from quantlab.models.registry import ExperimentLedger
from quantlab.research.envinfo import environment, git_commit, git_dirty
from quantlab.shadow.enums import ShadowMode
from quantlab.shadow.lineage import persist_shadow
from quantlab.shadow.models import ShadowRequest, ShadowResult
from quantlab.shadow.repository import persist
from quantlab.shadow.service import run_shadow_cycle
from quantlab.shadow.state import last_result


def _run_row(result: ShadowResult) -> ExperimentRun:
    first_order = result.orders[0].shadow_order_id if result.orders else ""
    first_fill = result.fills[0].shadow_fill_id if result.fills else ""
    return ExperimentRun(
        id=result.cycle.cycle_id,
        name=f"shadow:{result.cycle.mode.value}",
        hypothesis="Shadow execution is not broker execution.",
        status=ExperimentStatus.PASSED
        if result.cycle.status.value == "completed"
        else ExperimentStatus.FAILED,
        git_commit=git_commit(),
        dataset_version=result.cycle.data_snapshot_id,
        universe=sorted(result.portfolio.positions),
        feature_versions={"strategy": result.cycle.strategy_version},
        label_definition="not_applicable",
        hyperparameters={"seed": 0},
        transaction_cost_bps=10.0,
        snapshot_id=result.cycle.data_snapshot_id,
        data_kind="synthetic",
        data_snapshot_hash=result.cycle.data_snapshot_hash,
        metrics={
            "order_count": float(len(result.orders)),
            "fill_count": float(len(result.fills)),
            "cash": result.portfolio.cash,
            "equity": result.portfolio.equity,
            "data_freshness_ms": result.freshness.age_ms,
        },
        application_version=__version__,
        conclusion="shadow cycle; simulated fills only; not live",
        config_hash=result.cycle.configuration_hash,
        selection_stage="shadow",
        git_dirty=git_dirty(),
        python_version=environment().get("python", ""),
        research_type="shadow",
        decision_id=result.paper.run.decision_hash if result.paper else "",
        paper_account_id=result.paper_account.account_id,
        reconciliation_hash=result.reconciliation.reconciliation_hash,
        shadow_cycle_id=result.cycle.cycle_id,
        shadow_order_id=first_order,
        shadow_fill_id=first_fill,
        shadow_mode=result.cycle.mode.value,
        market_snapshot_hash=result.cycle.data_snapshot_hash,
        shadow_account_id=result.portfolio.account_id,
        production_run=result.cycle.production_run,
        data_freshness_ms=result.freshness.age_ms,
        decision_latency_ms=result.latency.market_to_decision_ms,
        execution_latency_ms=result.latency.order_to_fill_ms,
    )


def run_shadow_experiment(
    request: ShadowRequest | None = None,
    *,
    ledger_path: Path,
    append: bool = True,
) -> tuple[ShadowResult, ExperimentRun]:
    result = run_shadow_cycle(request)
    persist()
    with suppress(KnowledgeError):
        persist_shadow(result, ledger_path)
    row = _run_row(result)
    if append:
        ExperimentLedger(ledger_path).append(row)
    return result, row


def last_experiment_row() -> dict[str, str] | None:
    result = last_result()
    if result is None:
        return None
    return {
        "id": result.cycle.cycle_id,
        "mode": result.cycle.mode.value,
        "status": result.cycle.status.value,
        "recon": result.reconciliation.status,
        "orders": str(len(result.orders)),
        "fills": str(len(result.fills)),
        "hash": result.cycle.data_snapshot_hash,
    }


def seed_and_run(
    *,
    mode: ShadowMode = ShadowMode.RESEARCH_PAPER,
    ledger_path: Path,
) -> tuple[ShadowResult, ExperimentRun]:
    return run_shadow_experiment(ShadowRequest(mode=mode), ledger_path=ledger_path)
