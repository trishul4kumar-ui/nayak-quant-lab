"""Monitoring service. Consumes paper OMS observations; not a second backtester."""

from __future__ import annotations

from datetime import datetime

from quantlab.capital.definitions import InvestmentDecision, TargetPortfolio
from quantlab.core.config import LiveSafetyGates
from quantlab.core.errors import SafetyError
from quantlab.domain.research import IntegrityReport
from quantlab.monitoring.alpha_attribution import alpha_attribution
from quantlab.monitoring.attribution import security_attribution
from quantlab.monitoring.benchmark import equal_weight_universe, user_benchmark
from quantlab.monitoring.concentration import herfindahl
from quantlab.monitoring.drift import measure_drift
from quantlab.monitoring.enums import MonitoringRunStatus
from quantlab.monitoring.errors import MonitoringError, PerformanceReconciliationError
from quantlab.monitoring.exposure import exposure_map
from quantlab.monitoring.factor_attribution import factor_attribution
from quantlab.monitoring.feedback import build_feedback
from quantlab.monitoring.identity import hash_attribution, hash_pnl, hash_run, idempotency_key
from quantlab.monitoring.integrity import MonitoringLeakFlags
from quantlab.monitoring.library import seed_paper_result
from quantlab.monitoring.models import (
    EquityPoint,
    MonitoringRequest,
    MonitoringResult,
    MonitoringRun,
)
from quantlab.monitoring.performance import snapshot_from_account
from quantlab.monitoring.pnl import pnl_from_account
from quantlab.monitoring.reconciliation import reconcile_attribution, reconcile_pnl
from quantlab.monitoring.returns import report_returns, simple_return
from quantlab.monitoring.risk_monitor import risk_observation
from quantlab.monitoring.state import lookup, put_result
from quantlab.monitoring.turnover import fill_turnover
from quantlab.paper_oms.library import seed_snapshot
from quantlab.paper_oms.models import PaperOMSResult
from quantlab.research.integrity import evaluate_integrity


def _integrity(
    flags: MonitoringLeakFlags,
    *,
    live_trading: bool,
    data_kind: str,
) -> IntegrityReport:
    return evaluate_integrity(
        bars=[],
        states=[],
        as_of_times=[],
        next_bar_fill=True,
        cost_bps=10.0,
        slippage_model="configured",
        live_trading=live_trading,
        n_experiments_in_family=1,
        used_ml=False,
        data_kind=data_kind,
        future_performance_mark=flags.future_performance_mark,
        future_attribution_input=flags.future_attribution_input,
        future_benchmark=flags.future_benchmark,
        future_factor_return=flags.future_factor_return,
        performance_snapshot_mutation=flags.performance_snapshot_mutation,
        position_history_mutation=flags.position_history_mutation,
        pnl_reconciliation_break=flags.pnl_reconciliation_break,
        attribution_reconciliation_break=flags.attribution_reconciliation_break,
        hidden_residual=flags.hidden_residual,
        benchmark_lookahead=flags.benchmark_lookahead,
        target_observation_confusion=flags.target_observation_confusion,
        posthoc_attribution=flags.posthoc_attribution,
        performance_claim_overstatement=flags.performance_claim_overstatement,
    )


def run_monitoring(
    request: MonitoringRequest | None = None,
    *,
    paper: PaperOMSResult | None = None,
    decision: InvestmentDecision | None = None,
    target: TargetPortfolio | None = None,
    leaks: MonitoringLeakFlags | None = None,
    beginning_equity: float | None = None,
) -> MonitoringResult:
    used = request or MonitoringRequest()
    gates = LiveSafetyGates()
    if used.live_trading or gates.live_trading:
        raise SafetyError("LIVE_TRADING must remain false; monitoring does not trade")
    ignored = used.future_payload_ignored
    del ignored
    flags = leaks or MonitoringLeakFlags()
    if paper is None or decision is None or target is None:
        paper, decision, target = seed_paper_result()
        if used.oms_run_id not in {"", "last"} and paper.run.oms_run_id != used.oms_run_id:
            from quantlab.paper_oms.state import get_result as get_paper

            fetched = get_paper(used.oms_run_id)
            if fetched is None:
                raise MonitoringError(f"unknown paper OMS run {used.oms_run_id}")
            paper = fetched
    if target.decision_id != decision.decision_id:
        flags = flags.model_copy(update={"target_observation_confusion": True})
        raise MonitoringError("target_observation_confusion: target is not this decision")
    snapshot = seed_snapshot()
    key = idempotency_key(
        decision_hash=decision.decision_hash,
        oms_run_id=paper.run.oms_run_id,
        snapshot_id=paper.run.snapshot_id,
        methodology_id=used.methodology_id,
        benchmark_id="ew-universe-synthetic"
        if used.user_benchmark_returns is None
        else "user-supplied",
    )
    cached = lookup(key)
    if cached is not None:
        return cached

    start_equity = beginning_equity
    if start_equity is None:
        ledger = paper.account.ledger
        start_equity = ledger.opening_cash if ledger is not None else paper.account.equity
    pnl = pnl_from_account(paper.account, beginning_equity=start_equity, fills=paper.fills)
    attr = security_attribution(paper.account, pnl, paper.fills)
    factor = factor_attribution(
        pnl,
        factor_returns=used.factor_returns,
        factor_exposures=used.factor_exposures,
    )
    alpha = alpha_attribution(pnl, lineage=used.alpha_lineage)
    drift = measure_drift(target, paper.account, paper)
    conc = herfindahl(paper.account)
    turn = fill_turnover(paper.fills, equity=paper.account.equity)
    path = [
        EquityPoint(
            as_of=paper.run.started_at,
            cash=start_equity,
            market_value=0.0,
            equity=start_equity,
        ),
        EquityPoint(
            as_of=paper.run.completed_at,
            cash=paper.account.cash,
            reserved_cash=paper.account.reserved_cash,
            market_value=paper.account.market_value,
            equity=paper.account.equity,
        ),
    ]
    risk = risk_observation(paper.account, paper.fills, path)
    port_ret = simple_return(start_equity, paper.account.equity)
    if used.user_benchmark_returns is not None:
        bench = user_benchmark(used.user_benchmark_returns, portfolio_return=port_ret)
    else:
        bench = equal_weight_universe(snapshot, paper.account, beginning_equity=start_equity)
    returns = report_returns(
        beginning=start_equity,
        ending=paper.account.equity,
        period_returns=[] if port_ret is None else [port_ret],
        risk_free=used.risk_free_rate,
    )
    feedback = build_feedback(pnl, attr, factor, drift, concentration=conc, turnover=turn)
    pnl_breaks = reconcile_pnl(pnl)
    attr_breaks = reconcile_attribution(pnl, attr)
    if "pnl_reconciliation_break" in pnl_breaks:
        flags = flags.model_copy(update={"pnl_reconciliation_break": True})
        raise PerformanceReconciliationError("pnl identity failed")
    if "hidden_residual" in pnl_breaks:
        flags = flags.model_copy(update={"hidden_residual": True})
        raise PerformanceReconciliationError("residual hidden")
    if attr_breaks:
        flags = flags.model_copy(update={"attribution_reconciliation_break": True})
        raise PerformanceReconciliationError("attribution does not reconcile")
    if used.factor_returns and flags.future_factor_return:
        raise MonitoringError("future_factor_return")
    snap = snapshot_from_account(
        paper.account,
        pnl,
        as_of=paper.run.completed_at,
        snapshot_id=f"perf-{paper.run.oms_run_id}",
    )
    run = MonitoringRun(
        monitoring_run_id=f"MON-{paper.run.oms_run_id}",
        decision_hash=decision.decision_hash,
        oms_run_id=paper.run.oms_run_id,
        snapshot_id=paper.run.snapshot_id,
        methodology_id=used.methodology_id,
        as_of=used.as_of if isinstance(used.as_of, datetime) else paper.run.completed_at,
        status=MonitoringRunStatus.COMPLETE,
        performance_hash=hash_pnl(pnl),
        attribution_hash=hash_attribution(attr),
        live_trading=False,
    )
    run = run.model_copy(update={"run_hash": hash_run(run)})
    integrity = _integrity(flags, live_trading=False, data_kind=used.data_kind)
    del integrity
    result = MonitoringResult(
        run=run,
        snapshot=snap,
        pnl=pnl,
        returns=returns,
        attribution=attr,
        factor_attribution=factor,
        alpha_attribution=alpha,
        drift=drift,
        exposure=exposure_map(paper.account),
        concentration=conc,
        turnover=turn,
        drawdown=risk,
        benchmark=bench,
        feedback=feedback,
        reconciliation_ok=True,
        live_trading=False,
    )
    return put_result(result, key=key)
