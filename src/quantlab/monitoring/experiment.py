"""Monitoring ledger rows. Reuses JSONL ExperimentLedger."""

from __future__ import annotations

from pathlib import Path

from quantlab import __version__
from quantlab.capital.definitions import InvestmentDecision, TargetPortfolio
from quantlab.domain.models import ExperimentRun, ExperimentStatus
from quantlab.models.registry import ExperimentLedger
from quantlab.monitoring.library import seed_paper_result
from quantlab.monitoring.models import MonitoringRequest, MonitoringResult
from quantlab.monitoring.repository import persist
from quantlab.monitoring.service import run_monitoring
from quantlab.paper_oms.models import PaperOMSResult
from quantlab.research.envinfo import environment, git_commit, git_dirty


def _run_row(result: MonitoringResult, decision: InvestmentDecision) -> ExperimentRun:
    return ExperimentRun(
        id=result.run.monitoring_run_id,
        name=f"monitoring:{result.run.methodology_id}",
        hypothesis="Performance is evidence about an observed book, not proof of alpha.",
        status=ExperimentStatus.PASSED if result.reconciliation_ok else ExperimentStatus.FAILED,
        git_commit=git_commit(),
        dataset_version=result.run.snapshot_id,
        universe=sorted(result.exposure),
        feature_versions={"methodology": result.run.methodology_id},
        label_definition="not_applicable",
        hyperparameters={"risk_free": 0.0},
        transaction_cost_bps=10.0,
        random_seed=0,
        hypothesis_id="H-MOM-001",
        snapshot_id=result.run.snapshot_id,
        data_kind="synthetic",
        metrics={
            "pnl_total": result.pnl.pnl_total,
            "residual_pnl": result.pnl.residual_pnl,
            "net_return": result.pnl.net_return or 0.0,
            "max_drawdown": result.drawdown.max_drawdown,
        },
        application_version=__version__,
        conclusion="monitoring observation; not a promotion decision",
        config_hash=result.run.run_hash,
        selection_stage="monitoring",
        git_dirty=git_dirty(),
        python_version=environment().get("python", ""),
        tested_count=len(result.attribution.contributions),
        research_type="monitoring",
        decision_id=decision.decision_id,
        decision_hash=decision.decision_hash,
        oms_run_id=result.run.oms_run_id,
        monitoring_run_id=result.run.monitoring_run_id,
        performance_snapshot_id=result.snapshot.snapshot_id,
        performance_hash=result.run.performance_hash,
        attribution_hash=result.run.attribution_hash,
        target_portfolio_hash=decision.decision_hash,
        observed_portfolio_hash=result.snapshot.snapshot_hash,
        benchmark_id=result.benchmark.benchmark_id,
        attribution_method=result.attribution.method.value,
        residual_pnl=result.pnl.residual_pnl,
        research_feedback_id=result.feedback[0].feedback_id if result.feedback else "",
        knowledge_snapshot_id=decision.knowledge_snapshot_id,
    )


def run_monitoring_experiment(
    request: MonitoringRequest | None = None,
    *,
    ledger_path: Path,
    paper: PaperOMSResult | None = None,
    decision: InvestmentDecision | None = None,
    target: TargetPortfolio | None = None,
    append: bool = True,
) -> tuple[MonitoringResult, ExperimentRun]:
    if paper is None or decision is None or target is None:
        paper, decision, target = seed_paper_result()
    result = run_monitoring(request, paper=paper, decision=decision, target=target)
    persist()
    row = _run_row(result, decision)
    if append:
        ExperimentLedger(ledger_path).append(row)
    return result, row
