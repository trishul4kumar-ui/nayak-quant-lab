"""Capital allocation pipeline. Research/decision only. No orders."""

from __future__ import annotations

from pydantic import BaseModel

from quantlab import __version__
from quantlab.capital.abstention import reason_for
from quantlab.capital.budgets import (
    account_gross,
    account_net,
    investable_capital,
    notionals,
    opening_books,
)
from quantlab.capital.constraints import enforce_hard, evaluate_constraints
from quantlab.capital.decision import freeze_decision
from quantlab.capital.definitions import (
    AbstentionCode,
    AllocationRequest,
    CapitalAllocationState,
    CapitalPolicy,
    ConstraintCheck,
    DecisionStatus,
    DrawdownState,
    ExpectedReturn,
    InvestmentDecision,
    LiquidityStatus,
    TargetPortfolio,
)
from quantlab.capital.diagnostics import (
    AllocationDiagnostics,
    efficiency,
    expected_shortfall_interface,
    explain_name,
    risk_view,
    utilization,
)
from quantlab.capital.drawdown import allocation_state, classify_drawdown, multiplier, scale_weights
from quantlab.capital.errors import CapitalError, InfeasibleCapitalAllocation
from quantlab.capital.exposure import portfolio_exposure
from quantlab.capital.identity import request_identity
from quantlab.capital.integrity import CapitalLeakFlags
from quantlab.capital.library import get_policy
from quantlab.capital.liquidity import portfolio_liquidity
from quantlab.capital.sizing import size_positions
from quantlab.capital.turnover import apply_band, apply_min_trade, estimate_turnover
from quantlab.capital.validation import cap_synthetic, map_gate
from quantlab.capital.volatility_target import target_volatility
from quantlab.core.config import LiveSafetyGates
from quantlab.core.errors import SafetyError
from quantlab.domain.research import CheckResult, IntegrityReport
from quantlab.research.integrity import evaluate_integrity


class AllocationResult(BaseModel):
    decision: InvestmentDecision
    target: TargetPortfolio
    diagnostics: AllocationDiagnostics
    integrity: IntegrityReport
    expected_return: ExpectedReturn


def assert_research_path(*, live_trading: bool) -> None:
    gates = LiveSafetyGates()
    if live_trading or gates.live_trading:
        raise SafetyError(
            "Prompt 17 refuses to initialize production allocation while live_trading is true"
        )


def _integrity(flags: CapitalLeakFlags, *, live_trading: bool, data_kind: str) -> IntegrityReport:
    return evaluate_integrity(
        bars=[],
        states=[],
        as_of_times=[],
        next_bar_fill=True,
        cost_bps=10.0,
        slippage_model="none",
        live_trading=live_trading,
        n_experiments_in_family=1,
        used_ml=False,
        data_kind=data_kind,
        future_capital_input=flags.future_capital_input,
        future_risk_input=flags.future_risk_input,
        future_expected_return=flags.future_expected_return,
        future_factor_exposure=flags.future_factor_exposure,
        future_liquidity=flags.future_liquidity,
        future_turnover_state=flags.future_turnover_state,
        future_drawdown_state=flags.future_drawdown_state,
        future_constraint_parameter=flags.future_constraint_parameter,
        future_position_reference=flags.future_position_reference,
        future_decision_state=flags.future_decision_state,
        capital_policy_mutation=flags.capital_policy_mutation,
        decision_mutation=flags.decision_mutation,
        decision_hash_mismatch=flags.decision_hash_mismatch,
        allocation_lineage_break=flags.allocation_lineage_break,
        hidden_constraint_relaxation=flags.hidden_constraint_relaxation,
        silent_fallback=flags.silent_fallback,
        unknown_liquidity_as_infinite=flags.unknown_liquidity_as_infinite,
        unknown_factor_as_zero=flags.unknown_factor_as_zero,
        synthetic_capital_overpromotion=flags.synthetic_capital_overpromotion,
        gate_bypass=flags.gate_bypass,
        abstention_suppression=flags.abstention_suppression,
        future_portfolio_state=flags.future_portfolio_state,
        future_execution_cost=flags.future_execution_cost,
    )


def _finish(
    *,
    request: AllocationRequest,
    policy: CapitalPolicy,
    status: DecisionStatus,
    weights: dict[str, float],
    books_investable: float,
    books_equity: float,
    books_cash: float,
    code: AbstentionCode,
    stage: str,
    warnings: list[str],
    stages: list[str],
    constraints: list[ConstraintCheck],
    liquidity: LiquidityStatus,
    capital_state: CapitalAllocationState,
    drawdown_state: DrawdownState,
    method: str,
    vol: float | None,
    vol_status: str,
    factor: float | None,
    factor_status: CheckResult,
    risk_contrib: dict[str, float],
    turnover: float,
    flags: CapitalLeakFlags,
    expected: ExpectedReturn,
    diagnostics: AllocationDiagnostics,
) -> AllocationResult:
    status, extra = cap_synthetic(status, request.data_kind)
    warnings = [*warnings, *extra]
    if request.data_kind == "synthetic" and status in {
        DecisionStatus.ELIGIBLE,
        DecisionStatus.ALLOCATED,
        DecisionStatus.PAPER_READY,
    }:
        flags = flags.model_copy(update={"synthetic_capital_overpromotion": True})
        status = DecisionStatus.RESEARCH_ONLY
        warnings.append("synthetic cannot promote through Prompt 17")
    if status is DecisionStatus.ELIGIBLE and weights:
        status = DecisionStatus.ALLOCATED
    if request.data_kind == "synthetic" and status is DecisionStatus.ALLOCATED:
        status = DecisionStatus.RESEARCH_ONLY
        warnings.append("synthetic target is research diagnostics only")
    books = request.books or opening_books(policy)
    gross = account_gross(weights, books, books_investable) if weights else 0.0
    net = account_net(weights, books, books_investable) if weights else 0.0
    notional = notionals(weights, books_investable) if weights else {}
    cash_target = books_equity - sum(notional.values())
    draft = InvestmentDecision(
        decision_id="pending",
        decision_time=request.as_of,
        snapshot_id=request.snapshot_id,
        experiment_id=request.experiment_id,
        research_result_id=request.research_result_id,
        knowledge_snapshot_id=request.knowledge_snapshot_id,
        strategy_id=request.strategy_id,
        ensemble_id=request.ensemble_id,
        portfolio_spec_id=request.portfolio_spec_id,
        risk_policy_id=request.risk_policy_id,
        capital_policy_id=policy.policy_id,
        decision_status=status,
        input_alpha_version=request.input_alpha_version,
        risk_model_version=request.risk_model_version,
        covariance_version=request.covariance_version,
        regime_version=request.regime_version,
        execution_model_version=request.execution_model_version,
        expected_return=dict(expected.values),
        expected_return_source=expected.source.value,
        expected_risk=vol,
        expected_volatility=vol,
        gross_target=gross,
        net_target=net,
        target_weights=dict(weights),
        risk_contribution=risk_contrib,
        factor_exposure=factor,
        factor_exposure_status=factor_status,
        constraint_status=constraints,
        turnover_estimate=turnover,
        liquidity_status=liquidity,
        confidence=request.confidence.allocation_confidence(),
        evidence_status=request.data_kind,
        abstention_code=code,
        abstention_reason=reason_for(code) if code is not AbstentionCode.NONE else "",
        abstention_stage=stage,
        capital_state=capital_state,
        drawdown_state=drawdown_state,
        allocation_method=method,
        data_kind=request.data_kind,
        warnings=warnings,
        stages=stages,
        config_hash=policy.config_hash,
        created_at=request.as_of,
        software_version=__version__,
        live_trading=False,
    )
    decision = freeze_decision(draft)
    target = TargetPortfolio(
        portfolio_id=f"TP-{decision.decision_id}",
        decision_id=decision.decision_id,
        timestamp=request.as_of,
        weights=dict(weights),
        notional_targets=notional,
        gross_exposure=gross,
        net_exposure=net,
        cash_target=cash_target,
        risk_target=policy.target_volatility,
        turnover_estimate=turnover,
        constraint_state=constraints,
        portfolio_hash=decision.decision_hash,
    )
    diagnostics.vol_status = vol_status
    diagnostics.warnings = warnings
    diagnostics.stages = stages
    integrity = _integrity(flags, live_trading=False, data_kind=request.data_kind)
    return AllocationResult(
        decision=decision,
        target=target,
        diagnostics=diagnostics,
        integrity=integrity,
        expected_return=expected,
    )


def allocate(
    request: AllocationRequest,
    *,
    policy: CapitalPolicy | None = None,
    leaks: CapitalLeakFlags | None = None,
) -> AllocationResult:
    assert_research_path(live_trading=request.live_trading)
    _ = request.future_payload_ignored
    used = policy or get_policy(request.policy_id)
    flags = leaks or CapitalLeakFlags(
        future_capital_input=False,
        future_risk_input=False,
        future_expected_return=False,
        future_factor_exposure=False,
        future_liquidity=False,
        future_turnover_state=False,
        future_drawdown_state=False,
        future_constraint_parameter=False,
        future_position_reference=False,
        future_decision_state=False,
        capital_policy_mutation=False,
        decision_mutation=False,
        decision_hash_mismatch=False,
        allocation_lineage_break=False,
        hidden_constraint_relaxation=False,
        silent_fallback=False,
        unknown_liquidity_as_infinite=False,
        unknown_factor_as_zero=False,
        synthetic_capital_overpromotion=False,
        gate_bypass=False,
        abstention_suppression=False,
        future_portfolio_state=False,
        future_execution_cost=False,
    )
    stages = [
        "research_inputs",
        "input_validation",
        "pit_snapshot_freeze",
        "research_gate_check",
    ]
    books = request.books or opening_books(used)
    try:
        investable = investable_capital(books, used)
    except CapitalError:
        return _finish(
            request=request,
            policy=used,
            status=DecisionStatus.ABSTAIN,
            weights={},
            books_investable=0.0,
            books_equity=books.equity,
            books_cash=books.cash,
            code=AbstentionCode.CAPITAL_INSUFFICIENT,
            stage="capital_budget",
            warnings=[],
            stages=stages,
            constraints=[],
            liquidity=LiquidityStatus.UNKNOWN,
            capital_state=CapitalAllocationState.ABSTAIN,
            drawdown_state=classify_drawdown(request.drawdown, used.drawdown_limits),
            method=used.sizing_method.value,
            vol=None,
            vol_status="not_tested",
            factor=None,
            factor_status=CheckResult.NOT_TESTED,
            risk_contrib={},
            turnover=0.0,
            flags=flags,
            expected=ExpectedReturn(),
            diagnostics=AllocationDiagnostics(),
        )
    request_identity(request)
    gate_status, gate_code, gate_warnings = map_gate(
        request.gate,
        request.data_kind,
        allow_research_only_on_warn=used.constraint_policy.allow_research_only_on_warn,
    )
    if gate_code is AbstentionCode.GATE_FAIL:
        flags = flags.model_copy(update={"gate_bypass": False})
        return _finish(
            request=request,
            policy=used,
            status=DecisionStatus.REJECTED,
            weights={},
            books_investable=investable,
            books_equity=books.equity,
            books_cash=books.cash,
            code=AbstentionCode.GATE_FAIL,
            stage="research_gate_check",
            warnings=gate_warnings,
            stages=stages,
            constraints=[],
            liquidity=LiquidityStatus.UNKNOWN,
            capital_state=CapitalAllocationState.ABSTAIN,
            drawdown_state=classify_drawdown(request.drawdown, used.drawdown_limits),
            method=used.sizing_method.value,
            vol=None,
            vol_status="not_tested",
            factor=None,
            factor_status=CheckResult.NOT_TESTED,
            risk_contrib={},
            turnover=0.0,
            flags=flags,
            expected=ExpectedReturn(),
            diagnostics=AllocationDiagnostics(),
        )
    names = sorted(request.scores)
    if not names or all(request.scores[n] == 0 for n in names):
        return _finish(
            request=request,
            policy=used,
            status=DecisionStatus.ABSTAIN,
            weights={},
            books_investable=investable,
            books_equity=books.equity,
            books_cash=books.cash,
            code=AbstentionCode.EXPECTED_RETURN_UNAVAILABLE,
            stage="expected_return_normalization",
            warnings=gate_warnings,
            stages=[*stages, "expected_return_normalization"],
            constraints=[],
            liquidity=LiquidityStatus.UNKNOWN,
            capital_state=CapitalAllocationState.ABSTAIN,
            drawdown_state=classify_drawdown(request.drawdown, used.drawdown_limits),
            method=used.sizing_method.value,
            vol=None,
            vol_status="not_tested",
            factor=None,
            factor_status=CheckResult.NOT_TESTED,
            risk_contrib={},
            turnover=0.0,
            flags=flags,
            expected=ExpectedReturn(source=request.expected_return_source),
            diagnostics=AllocationDiagnostics(),
        )
    expected = ExpectedReturn(
        values={name: request.scores[name] for name in names},
        source=request.expected_return_source,
        horizon=request.expected_return_horizon,
        confidence=request.expected_return_confidence,
        override_recorded=request.expected_return_source.value == "research_override",
    )
    stages.append("expected_return_normalization")
    if request.expected_return_source.value == "research_override" and request.gate is not None:
        stages.append("override_recorded_gate_still_binds")
    confidence = request.confidence.allocation_confidence()
    conf_pol = used.confidence_policy
    if confidence < conf_pol.abstain_below:
        return _finish(
            request=request,
            policy=used,
            status=DecisionStatus.ABSTAIN,
            weights={},
            books_investable=investable,
            books_equity=books.equity,
            books_cash=books.cash,
            code=AbstentionCode.CONFIDENCE_BELOW_THRESHOLD,
            stage="confidence",
            warnings=gate_warnings,
            stages=stages,
            constraints=[],
            liquidity=LiquidityStatus.UNKNOWN,
            capital_state=CapitalAllocationState.ABSTAIN,
            drawdown_state=classify_drawdown(request.drawdown, used.drawdown_limits),
            method=used.sizing_method.value,
            vol=None,
            vol_status="not_tested",
            factor=None,
            factor_status=CheckResult.NOT_TESTED,
            risk_contrib={},
            turnover=0.0,
            flags=flags,
            expected=expected,
            diagnostics=AllocationDiagnostics(),
        )
    dd_state = classify_drawdown(request.drawdown, used.drawdown_limits)
    cap_state = allocation_state(dd_state)
    if cap_state is CapitalAllocationState.HALT:
        hold = dict(request.previous_weights)
        return _finish(
            request=request,
            policy=used,
            status=DecisionStatus.ABSTAIN,
            weights=hold,
            books_investable=investable,
            books_equity=books.equity,
            books_cash=books.cash,
            code=AbstentionCode.DRAWDOWN_HALT,
            stage="drawdown_capital_state",
            warnings=[*gate_warnings, "no new exposure; Prompt 17 does not auto-liquidate"],
            stages=[*stages, "drawdown_capital_state"],
            constraints=[],
            liquidity=LiquidityStatus.UNKNOWN,
            capital_state=CapitalAllocationState.HALT,
            drawdown_state=dd_state,
            method=used.sizing_method.value,
            vol=None,
            vol_status="not_tested",
            factor=None,
            factor_status=CheckResult.NOT_TESTED,
            risk_contrib={},
            turnover=estimate_turnover(request.previous_weights, hold),
            flags=flags,
            expected=expected,
            diagnostics=AllocationDiagnostics(),
        )
    stages.extend(["risk_estimation", "risk_budget", "capital_budget", "position_sizing"])
    if used.constraint_policy.strict_missing_covariance and request.covariance is None:
        return _finish(
            request=request,
            policy=used,
            status=DecisionStatus.ABSTAIN,
            weights={},
            books_investable=investable,
            books_equity=books.equity,
            books_cash=books.cash,
            code=AbstentionCode.COVARIANCE_INVALID,
            stage="risk_estimation",
            warnings=gate_warnings,
            stages=stages,
            constraints=[],
            liquidity=LiquidityStatus.UNKNOWN,
            capital_state=cap_state,
            drawdown_state=dd_state,
            method=used.sizing_method.value,
            vol=None,
            vol_status="not_tested",
            factor=None,
            factor_status=CheckResult.NOT_TESTED,
            risk_contrib={},
            turnover=0.0,
            flags=flags,
            expected=expected,
            diagnostics=AllocationDiagnostics(),
        )
    sizing = size_positions(names, request, used, confidence=confidence)
    weights = dict(sizing.output_weights)
    drag = sum(request.execution_cost.get(n, 0.0) * abs(weights.get(n, 0.0)) for n in names)
    port_mu = sum(expected.values.get(n, 0.0) * weights.get(n, 0.0) for n in names)
    if drag > 0 and port_mu > 0 and drag >= port_mu:
        return _finish(
            request=request,
            policy=used,
            status=DecisionStatus.ABSTAIN,
            weights={},
            books_investable=investable,
            books_equity=books.equity,
            books_cash=books.cash,
            code=AbstentionCode.EXECUTION_DRAG,
            stage="execution_cost",
            warnings=gate_warnings,
            stages=[*stages, "execution_cost"],
            constraints=[],
            liquidity=LiquidityStatus.UNKNOWN,
            capital_state=cap_state,
            drawdown_state=dd_state,
            method=sizing.method_id,
            vol=None,
            vol_status="not_tested",
            factor=None,
            factor_status=CheckResult.NOT_TESTED,
            risk_contrib={},
            turnover=0.0,
            flags=flags,
            expected=expected,
            diagnostics=AllocationDiagnostics(),
        )
    stages.append("liquidity_filter")
    liq_status, _per = portfolio_liquidity(
        notionals(weights, investable),
        request.liquidity_adv,
        used.liquidity_policy,
    )
    if liq_status is LiquidityStatus.UNKNOWN and used.liquidity_policy.strict_unknown:
        flags = flags.model_copy(update={"unknown_liquidity_as_infinite": False})
        return _finish(
            request=request,
            policy=used,
            status=DecisionStatus.ABSTAIN,
            weights={},
            books_investable=investable,
            books_equity=books.equity,
            books_cash=books.cash,
            code=AbstentionCode.UNKNOWN_LIQUIDITY,
            stage="liquidity_filter",
            warnings=gate_warnings,
            stages=stages,
            constraints=[],
            liquidity=LiquidityStatus.UNKNOWN,
            capital_state=cap_state,
            drawdown_state=dd_state,
            method=sizing.method_id,
            vol=None,
            vol_status="not_tested",
            factor=None,
            factor_status=CheckResult.NOT_TESTED,
            risk_contrib={},
            turnover=0.0,
            flags=flags,
            expected=expected,
            diagnostics=AllocationDiagnostics(),
        )
    if liq_status is LiquidityStatus.INSUFFICIENT and used.liquidity_policy.abstain_on_insufficient:
        return _finish(
            request=request,
            policy=used,
            status=DecisionStatus.ABSTAIN,
            weights={},
            books_investable=investable,
            books_equity=books.equity,
            books_cash=books.cash,
            code=AbstentionCode.UNKNOWN_LIQUIDITY,
            stage="liquidity_filter",
            warnings=[*gate_warnings, "participation limit breached"],
            stages=stages,
            constraints=[],
            liquidity=LiquidityStatus.INSUFFICIENT,
            capital_state=cap_state,
            drawdown_state=dd_state,
            method=sizing.method_id,
            vol=None,
            vol_status="not_tested",
            factor=None,
            factor_status=CheckResult.NOT_TESTED,
            risk_contrib={},
            turnover=0.0,
            flags=flags,
            expected=expected,
            diagnostics=AllocationDiagnostics(),
        )
    factor, factor_status = portfolio_exposure(weights, request.factor_exposures)
    if used.constraint_policy.strict_unknown_factor and factor_status is CheckResult.NOT_TESTED:
        flags = flags.model_copy(update={"unknown_factor_as_zero": False})
        return _finish(
            request=request,
            policy=used,
            status=DecisionStatus.ABSTAIN,
            weights={},
            books_investable=investable,
            books_equity=books.equity,
            books_cash=books.cash,
            code=AbstentionCode.UNKNOWN_FACTOR,
            stage="factor_exposure",
            warnings=gate_warnings,
            stages=stages,
            constraints=[],
            liquidity=liq_status,
            capital_state=cap_state,
            drawdown_state=dd_state,
            method=sizing.method_id,
            vol=None,
            vol_status="not_tested",
            factor=None,
            factor_status=factor_status,
            risk_contrib={},
            turnover=0.0,
            flags=flags,
            expected=expected,
            diagnostics=AllocationDiagnostics(),
        )
    stages.extend(["constraint_engine", "portfolio_optimization", "volatility_targeting"])
    vol_result = target_volatility(
        weights, request.covariance, used.target_volatility, used.gross_leverage_limit
    )
    weights = vol_result.weights
    stages.append("turnover_control")
    weights = apply_band(request.previous_weights, weights, used.rebalance_band)
    weights = apply_min_trade(request.previous_weights, weights, used.min_trade_threshold)
    stages.append("drawdown_capital_state")
    scale = multiplier(cap_state, used.allocation_multipliers)
    if confidence < conf_pol.reduce_below:
        scale *= 0.5
    weights = scale_weights(weights, scale)
    turnover = estimate_turnover(request.previous_weights, weights)
    beta, beta_status = portfolio_exposure(weights, request.factor_exposures)
    checks = evaluate_constraints(
        weights,
        used,
        books,
        investable,
        request.previous_weights,
        beta=beta,
        beta_status=beta_status,
        factor=factor,
        factor_status=factor_status,
        sector_status=CheckResult.NOT_TESTED,
        shortability_status=CheckResult.NOT_TESTED,
    )
    try:
        enforce_hard(checks, weights)
    except InfeasibleCapitalAllocation:
        if used.constraint_policy.abstain_on_infeasible:
            return _finish(
                request=request,
                policy=used,
                status=DecisionStatus.ABSTAIN,
                weights={},
                books_investable=investable,
                books_equity=books.equity,
                books_cash=books.cash,
                code=AbstentionCode.CONSTRAINT_INFEASIBLE,
                stage="constraint_engine",
                warnings=gate_warnings,
                stages=stages,
                constraints=checks,
                liquidity=liq_status,
                capital_state=cap_state,
                drawdown_state=dd_state,
                method=sizing.method_id,
                vol=vol_result.estimated_vol,
                vol_status=vol_result.status.value,
                factor=factor,
                factor_status=factor_status,
                risk_contrib={},
                turnover=turnover,
                flags=flags,
                expected=expected,
                diagnostics=AllocationDiagnostics(),
            )
        if used.constraint_policy.fallback_sizing:
            raise
        flags = flags.model_copy(
            update={"hidden_constraint_relaxation": False, "silent_fallback": False}
        )
        raise
    stages.append("abstention_check")
    risk = risk_view(weights, request.covariance)
    contrib: dict[str, float] = {}
    raw_contrib = risk.get("contributions", [])
    if isinstance(raw_contrib, list):
        for item in raw_contrib:
            if isinstance(item, dict):
                sid = str(item.get("security_id", ""))
                contrib[sid] = float(item.get("component") or 0.0)
    var_est, var_status = expected_shortfall_interface(request.n_obs_returns)
    explanations = [
        explain_name(
            name,
            weights.get(name, 0.0),
            request,
            used,
            binding="none",
            status=gate_status.value,
        )
        for name in names
    ]
    diagnostics = AllocationDiagnostics(
        stages=stages,
        utilization=utilization(
            gross=account_gross(weights, books, investable),
            gross_limit=used.gross_leverage_limit,
            vol=vol_result.estimated_vol,
            target_vol=used.target_volatility,
            turnover=turnover,
            max_turnover=used.max_turnover,
            cash_used=investable,
            equity=books.equity,
        ),
        efficiency=efficiency(port_mu, books.equity, vol_result.estimated_vol, turnover, drag),
        attribution={
            "alpha": sizing.method_id,
            "risk": used.risk_budget_method.value,
            "capital_state": cap_state.value,
            "execution_cost": "separate_from_mu",
        },
        explanations=explanations,
        var_status=var_status,
        es_status=var_status,
        var_estimate=var_est,
        es_estimate=var_est,
        vol_status=vol_result.status.value,
        warnings=gate_warnings,
    )
    final_status = gate_status
    if final_status is DecisionStatus.ELIGIBLE:
        final_status = DecisionStatus.ALLOCATED
    return _finish(
        request=request,
        policy=used,
        status=final_status,
        weights=weights,
        books_investable=investable,
        books_equity=books.equity,
        books_cash=books.cash,
        code=AbstentionCode.NONE,
        stage="",
        warnings=gate_warnings,
        stages=stages,
        constraints=checks,
        liquidity=liq_status,
        capital_state=cap_state,
        drawdown_state=dd_state,
        method=sizing.method_id,
        vol=vol_result.estimated_vol,
        vol_status=vol_result.status.value,
        factor=factor,
        factor_status=factor_status,
        risk_contrib=contrib,
        turnover=turnover,
        flags=flags,
        expected=expected,
        diagnostics=diagnostics,
    )
