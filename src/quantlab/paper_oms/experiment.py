"""Paper OMS ledger rows. Reuses JSONL ExperimentLedger. Not a second ledger."""

from __future__ import annotations

from pathlib import Path

from quantlab import __version__
from quantlab.capital.definitions import InvestmentDecision, TargetPortfolio
from quantlab.domain.models import ExperimentRun, ExperimentStatus
from quantlab.models.registry import ExperimentLedger
from quantlab.paper_oms.library import seed_account, seed_decision, seed_snapshot, seed_target
from quantlab.paper_oms.models import (
    PaperAccount,
    PaperMarketSnapshot,
    PaperOMSRequest,
    PaperOMSResult,
)
from quantlab.paper_oms.repository import persist
from quantlab.paper_oms.service import run_paper_oms
from quantlab.paper_oms.state import last_result
from quantlab.research.envinfo import environment, git_commit, git_dirty
from quantlab.risk.firewall import RiskFirewall


def _run_row(result: PaperOMSResult, decision: InvestmentDecision) -> ExperimentRun:
    return ExperimentRun(
        id=result.run.oms_run_id,
        name=f"paper_oms:{result.run.execution_policy_id}",
        hypothesis="Paper OMS is order lifecycle simulation, not a broker.",
        status=ExperimentStatus.PASSED
        if result.reconciliation.status.value == "reconciled"
        else ExperimentStatus.FAILED,
        git_commit=git_commit(),
        dataset_version=result.run.snapshot_id,
        universe=sorted(result.account.positions),
        feature_versions={"execution_policy": result.run.execution_policy_id},
        label_definition="not_applicable",
        hyperparameters={"seed": result.run.random_seed},
        transaction_cost_bps=10.0,
        random_seed=result.run.random_seed,
        hypothesis_id="H-MOM-001",
        snapshot_id=result.run.snapshot_id,
        data_kind="synthetic",
        metrics={
            "order_count": float(result.run.order_count),
            "fill_count": float(result.run.fill_count),
            "cash": result.account.cash,
            "equity": result.account.equity,
        },
        application_version=__version__,
        conclusion=f"paper oms {result.run.status.value}; simulated fills only",
        config_hash=result.run.run_hash,
        selection_stage="paper_oms",
        git_dirty=git_dirty(),
        python_version=environment().get("python", ""),
        tested_count=result.run.order_count,
        research_type="paper_oms",
        execution_model_id=result.run.execution_policy_id,
        scenario_id=result.run.execution_policy_id,
        decision_id=decision.decision_id,
        oms_run_id=result.run.oms_run_id,
        order_plan_hash=result.run.order_plan_hash,
        paper_account_id=result.account.account_id,
        reconciliation_hash=result.reconciliation.reconciliation_hash,
        decision_hash=decision.decision_hash,
        knowledge_snapshot_id=decision.knowledge_snapshot_id,
    )


def run_paper_experiment(
    request: PaperOMSRequest | None = None,
    *,
    ledger_path: Path,
    decision: InvestmentDecision | None = None,
    target: TargetPortfolio | None = None,
    account: PaperAccount | None = None,
    snapshot: PaperMarketSnapshot | None = None,
    firewall: RiskFirewall | None = None,
    append: bool = True,
) -> tuple[PaperOMSResult, ExperimentRun]:
    used_decision = decision or seed_decision()
    used_target = target or seed_target()
    result = run_paper_oms(
        request,
        decision=used_decision,
        target=used_target,
        account=account or seed_account(),
        snapshot=snapshot or seed_snapshot(),
        firewall=firewall,
    )
    persist(ledger_path.with_name("paper_oms_state.json"))
    row = _run_row(result, used_decision)
    if append:
        ExperimentLedger(ledger_path).append(row)
    return result, row


def last_experiment_row() -> dict[str, str] | None:
    result = last_result()
    if result is None:
        return None
    return {
        "id": result.run.oms_run_id,
        "status": result.run.status.value,
        "recon": result.reconciliation.status.value,
        "orders": str(result.run.order_count),
        "fills": str(result.run.fill_count),
        "hash": result.run.run_hash,
    }
