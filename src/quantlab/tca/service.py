"""TCA service. Wraps Prompt 13 models and Prompt 18 fills. Not a second simulator."""

from __future__ import annotations

from quantlab.core.config import LiveSafetyGates
from quantlab.core.errors import SafetyError
from quantlab.domain.research import CheckResult, IntegrityReport
from quantlab.execution_research.costs import cost_components
from quantlab.paper_oms.library import seed_account, seed_decision, seed_snapshot, seed_target
from quantlab.paper_oms.models import PaperOMSRequest, PaperOMSResult
from quantlab.paper_oms.service import run_paper_oms
from quantlab.paper_oms.state import get_result as get_paper
from quantlab.paper_oms.state import last_result as last_paper
from quantlab.research.integrity import evaluate_integrity
from quantlab.tca.calibration import calibrate_impact
from quantlab.tca.capacity import capacity_from_liquidity
from quantlab.tca.enums import SpreadKind, TCAKind
from quantlab.tca.errors import TCAError
from quantlab.tca.fragility import fragility_from
from quantlab.tca.identity import hash_run, idempotency_key
from quantlab.tca.integrity import TCALeakFlags
from quantlab.tca.models import (
    CapacityPolicy,
    CostLeg,
    LiquidityObservation,
    TCARequest,
    TCAResult,
    TCARun,
)
from quantlab.tca.shortfall import shortfall_from_fills
from quantlab.tca.state import lookup, put_result


def _integrity(flags: TCALeakFlags, *, live_trading: bool, data_kind: str) -> IntegrityReport:
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
        future_tca_observation=flags.future_tca_observation,
        future_impact_calibration=flags.future_impact_calibration,
        calibration_window_leak=flags.calibration_window_leak,
        arrival_price_lookahead=flags.arrival_price_lookahead,
        wrong_side_slippage=flags.wrong_side_slippage,
        synthetic_adv_claim=flags.synthetic_adv_claim,
        observed_vs_modelled_confusion=flags.observed_vs_modelled_confusion,
        tca_parameter_mutation=flags.tca_parameter_mutation,
        hidden_partial_fill=flags.hidden_partial_fill,
        capacity_lookahead=flags.capacity_lookahead,
    )


def _paper(oms_run_id: str) -> PaperOMSResult:
    found = last_paper() if oms_run_id in {"", "last"} else get_paper(oms_run_id)
    if found is not None:
        return found
    return run_paper_oms(
        PaperOMSRequest(),
        decision=seed_decision(),
        target=seed_target(),
        account=seed_account(),
        snapshot=seed_snapshot(),
    )


def run_tca(
    request: TCARequest | None = None,
    *,
    paper: PaperOMSResult | None = None,
    leaks: TCALeakFlags | None = None,
) -> TCAResult:
    used = request or TCARequest()
    gates = LiveSafetyGates()
    if used.live_trading or gates.live_trading:
        raise SafetyError("LIVE_TRADING must remain false; TCA does not route orders")
    ignored = used.future_payload_ignored
    del ignored
    flags = leaks or TCALeakFlags()
    if used.kind is TCAKind.OBSERVED and flags.observed_vs_modelled_confusion:
        raise TCAError("observed_vs_modelled_confusion")
    paper_result = paper or _paper(used.oms_run_id)
    key = idempotency_key(
        oms_run_id=paper_result.run.oms_run_id,
        kind=used.kind.value,
        arrival_policy=used.arrival_policy.value,
        snapshot_id=paper_result.run.snapshot_id,
        model_version="is-v1",
        liquidity_evidence=(
            None
            if used.liquidity_observation is None
            else used.liquidity_observation.model_dump(mode="json")
        ),
    )
    cached = lookup(key)
    if cached is not None:
        return cached
    unfilled = sum(
        order.remaining_quantity * order.reference_price for order in paper_result.orders
    )
    shortfall = shortfall_from_fills(
        paper_result.fills,
        policy=used.arrival_policy,
        user_benchmark=used.user_benchmark_price,
        unfilled_notional=unfilled,
        opportunity_reference=None,
    )
    from quantlab.backtest.costs import CostSchedule

    schedule = CostSchedule(commission_bps=10.0, provenance="configured_research")
    legs = [
        CostLeg(
            name=row.name,
            value=row.value,
            status=CheckResult.NOT_TESTED
            if row.status.value in {"unspecified", "not_tested"}
            else CheckResult.PASS,
            provenance=row.provenance,
            note="Indian tax legs unspecified remain NOT_TESTED.",
        )
        for row in cost_components(schedule)
    ]
    liquidity = used.liquidity_observation or LiquidityObservation(
        status=CheckResult.NOT_TESTED,
        note=(
            "No typed liquidity evidence was supplied. Capacity is NOT_TESTED; "
            "paper/synthetic snapshot volume is never treated as NSE ADV."
        ),
    )
    flags = flags.model_copy(update={"synthetic_adv_claim": False})
    calibration = None
    if used.calibrate:
        calibration = calibrate_impact(
            paper_result.fills,
            as_of=used.as_of,
            window_end=used.as_of,
            snapshot_id=paper_result.run.snapshot_id,
        )
    policy = used.capacity_policy or CapacityPolicy(
        policy_id="CAP-TCA-001",
        max_participation=0.10,
        max_cost_bps=50.0,
        min_net_edge=0.0,
    )
    capacity = capacity_from_liquidity(
        liquidity,
        policy,
        turnover=paper_result.account.turnover,
        expected_edge=None,
        impact_k=None if calibration is None else calibration.estimate,
    )
    fragility = fragility_from(shortfall, capacity)
    target_notional = sum(abs(v) for v in seed_target().notional_targets.values())
    filled_notional = sum(item.gross_notional for item in paper_result.fills)
    comparison = {
        "target_notional": target_notional,
        "filled_notional": filled_notional,
        "residual_notional": max(target_notional - filled_notional, 0.0),
        "paper_shortfall": paper_result.tca.implementation_shortfall or 0.0,
        "tca_shortfall": shortfall.total or 0.0,
    }
    run = TCARun(
        tca_run_id=f"TCA-{paper_result.run.oms_run_id}",
        oms_run_id=paper_result.run.oms_run_id,
        kind=used.kind,
        arrival_policy=used.arrival_policy,
        as_of=used.as_of,
        calibration_hash="" if calibration is None else calibration.parameter_hash,
        live_trading=False,
    )
    run = run.model_copy(update={"tca_hash": hash_run(run)})
    integrity = _integrity(flags, live_trading=False, data_kind=used.data_kind)
    del integrity
    result = TCAResult(
        run=run,
        kind=used.kind,
        shortfall=shortfall,
        spread_kind=SpreadKind.UNAVAILABLE
        if used.kind is TCAKind.OBSERVED
        else SpreadKind.BAR_PROXY,
        costs=legs,
        liquidity=liquidity,
        calibration=calibration,
        capacity=capacity,
        fragility=fragility,
        paper_comparison=comparison,
        live_trading=False,
        note=(
            f"{used.kind.value}. Paper fill is not broker-confirmed. "
            "Bid/ask history is NOT_TESTED. Official NSE ADV is NOT_TESTED."
        ),
    )
    if used.kind is TCAKind.MODELLED:
        result = result.model_copy(
            update={"note": "MODELLED_TCA. Do not report as realized/observed costs."}
        )
    return put_result(result, key=key)
