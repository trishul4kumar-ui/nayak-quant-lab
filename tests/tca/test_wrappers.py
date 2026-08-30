from __future__ import annotations

from datetime import UTC, datetime

import pytest

from quantlab.domain.models import Side
from quantlab.domain.research import CheckResult
from quantlab.paper_oms.models import PaperFill
from quantlab.tca.attribution import compare_paper
from quantlab.tca.calibration import calibrate_impact
from quantlab.tca.capacity import LADDER, capacity_from_liquidity
from quantlab.tca.enums import ArrivalPolicy, CapacityStatus, FragilityStatus, TCAKind
from quantlab.tca.estimation import mean_with_count
from quantlab.tca.fragility import fragility_from
from quantlab.tca.identity import hash_calibration
from quantlab.tca.latency import no_pre_arrival
from quantlab.tca.models import (
    CapacityPolicy,
    CapacityResult,
    CapacityScenario,
    LiquidityObservation,
    ShortfallBreakdown,
)
from quantlab.tca.shortfall import shortfall_from_fills
from quantlab.tca.uncertainty import interval


def _fill(
    *,
    side: Side = Side.BUY,
    arrival: float = 100.0,
    execution: float = 101.0,
    qty: float = 10.0,
    remaining: float = 0.0,
    fill_time: datetime | None = None,
    fill_id: str = "F1",
) -> PaperFill:
    when = fill_time or datetime(2024, 1, 15, tzinfo=UTC)
    return PaperFill(
        fill_id=fill_id,
        order_id="O1",
        security_id="NSE:AAA",
        side=side,
        requested_quantity=qty + remaining,
        filled_quantity=qty,
        remaining_quantity=remaining,
        reference_price=arrival,
        arrival_price=arrival,
        execution_price=execution,
        gross_notional=qty * execution,
        arrival_time=when,
        fill_time=when,
        execution_model_id="base",
        spread_cost=0.1,
        slippage_cost=abs(execution - arrival) * qty,
        impact_cost=0.0,
        commission=0.0,
        taxes=0.0,
        fees=0.0,
        total_cost=0.1,
    )


@pytest.mark.parametrize(
    ("module", "name"),
    [
        ("spread", "spread_bps"),
        ("slippage", "slippage_bps"),
        ("impact", "impact_bps"),
        ("fills", "simulate_fill"),
        ("costs", "explicit_bps"),
        ("liquidity", "liquidity_profile"),
        ("latency", "arrival_index"),
    ],
)
def test_prompt13_wrappers_are_canonical(module: str, name: str) -> None:
    import importlib

    tca = importlib.import_module(f"quantlab.tca.{module}")
    exe = importlib.import_module(f"quantlab.execution_research.{module}")
    assert getattr(tca, name) is getattr(exe, name)


def test_unavailable_arrival_is_not_tested() -> None:
    item = shortfall_from_fills(
        [_fill()],
        policy=ArrivalPolicy.UNAVAILABLE,
    )
    assert item.status is CheckResult.NOT_TESTED
    assert item.total is None


def test_partial_fill_opportunity_stays_unmeasured() -> None:
    fill = _fill(remaining=5.0)
    missing = shortfall_from_fills(
        [fill],
        policy=ArrivalPolicy.ARRIVAL_SNAPSHOT,
        unfilled_notional=500.0,
        opportunity_reference=None,
    )
    assert missing.opportunity_cost is None
    measured = shortfall_from_fills(
        [fill],
        policy=ArrivalPolicy.ARRIVAL_SNAPSHOT,
        unfilled_notional=500.0,
        opportunity_reference=1.0,
    )
    assert measured.opportunity_cost == 0.0
    assert "Opportunity cost is measurement after the fact" in measured.note


def test_future_fill_excluded_from_calibration() -> None:
    past = _fill()
    future = _fill(fill_time=datetime(2024, 6, 1, tzinfo=UTC), fill_id="F2")
    as_of = datetime(2024, 1, 15, tzinfo=UTC)
    with_future = calibrate_impact(
        [past, future],
        as_of=as_of,
        window_end=as_of,
        snapshot_id="seed",
    )
    without = calibrate_impact(
        [past],
        as_of=as_of,
        window_end=as_of,
        snapshot_id="seed",
    )
    assert with_future.sample_count == without.sample_count
    assert with_future.parameter_hash == without.parameter_hash
    assert with_future.frozen is True


def test_calibration_identity_changes_with_window() -> None:
    fills = [_fill()]
    as_of = datetime(2024, 1, 15, tzinfo=UTC)
    a = calibrate_impact(fills, as_of=as_of, window_end=as_of, snapshot_id="seed")
    b = calibrate_impact(
        fills,
        as_of=as_of,
        window_end=datetime(2024, 1, 14, tzinfo=UTC),
        snapshot_id="seed",
    )
    assert a.parameter_hash != b.parameter_hash
    assert hash_calibration(a) == a.parameter_hash


def test_capacity_with_synthetic_volume_is_labelled() -> None:
    result = capacity_from_liquidity(
        LiquidityObservation(volume=10_000_000.0),
        CapacityPolicy(
            policy_id="p",
            max_participation=0.1,
            max_cost_bps=50.0,
            min_net_edge=0.0,
        ),
        turnover=0.01,
        expected_edge=0.02,
        impact_k=0.05,
    )
    assert result.status is CapacityStatus.FEASIBLE
    assert len(result.scenarios) == len(LADDER)
    assert "not NSE ADV" in result.note
    assert "NSE ADV" not in result.note.replace("not NSE ADV", "")


def test_capacity_breach_when_participation_exceeds_policy() -> None:
    result = capacity_from_liquidity(
        LiquidityObservation(volume=1_000_000.0),
        CapacityPolicy(
            policy_id="tight",
            max_participation=0.05,
            max_cost_bps=1.0,
            min_net_edge=0.0,
        ),
        turnover=0.5,
        expected_edge=0.01,
        impact_k=1.0,
    )
    assert result.status is CapacityStatus.BREACH
    assert any(row.breach for row in result.scenarios)


def _capacity(*, status: CapacityStatus, breaches: int) -> CapacityResult:
    rows = [
        CapacityScenario(
            capital=capital,
            participation=0.01,
            estimated_impact_bps=1.0,
            expected_cost=1.0,
            net_edge=1.0,
            turnover=0.1,
            unfilled=None,
            breach=index < breaches,
        )
        for index, capital in enumerate(LADDER)
    ]
    return CapacityResult(policy_id="p", status=status, scenarios=rows)


def test_fragility_robust() -> None:
    out = fragility_from(
        ShortfallBreakdown(total=1.0, status=CheckResult.PASS),
        _capacity(status=CapacityStatus.FEASIBLE, breaches=0),
    )
    assert out.status is FragilityStatus.ROBUST


def test_fragility_fragile_on_many_breaches() -> None:
    out = fragility_from(
        ShortfallBreakdown(total=1.0, status=CheckResult.PASS),
        _capacity(status=CapacityStatus.FEASIBLE, breaches=4),
    )
    assert out.status is FragilityStatus.FRAGILE


def test_fragility_unviable_on_capacity_breach() -> None:
    out = fragility_from(
        ShortfallBreakdown(total=1.0, status=CheckResult.PASS),
        _capacity(status=CapacityStatus.BREACH, breaches=8),
    )
    assert out.status is FragilityStatus.ECONOMICALLY_UNVIABLE


def test_fragility_unviable_under_stress_multiplier() -> None:
    out = fragility_from(
        ShortfallBreakdown(total=1.0, status=CheckResult.PASS),
        _capacity(status=CapacityStatus.FEASIBLE, breaches=0),
        stressed_cost_mult=3.0,
    )
    assert out.status is FragilityStatus.ECONOMICALLY_UNVIABLE


def test_estimation_requires_eight_samples() -> None:
    assert mean_with_count([1.0] * 7) == (None, 7)
    estimate, count = mean_with_count([2.0] * 8)
    assert count == 8
    assert estimate == pytest.approx(2.0)


def test_latency_rejects_pre_arrival() -> None:
    decision = datetime(2024, 1, 15, tzinfo=UTC)
    arrival = datetime(2024, 1, 15, 1, tzinfo=UTC)
    fill = datetime(2024, 1, 15, 2, tzinfo=UTC)
    assert no_pre_arrival(decision, arrival, fill)
    assert not no_pre_arrival(decision, arrival, decision)


def test_paper_vs_tca_comparison_keys() -> None:
    from quantlab.paper_oms.library import seed_account, seed_decision, seed_snapshot, seed_target
    from quantlab.paper_oms.models import PaperOMSRequest
    from quantlab.paper_oms.service import run_paper_oms

    paper = run_paper_oms(
        PaperOMSRequest(),
        decision=seed_decision(),
        target=seed_target(),
        account=seed_account(),
        snapshot=seed_snapshot(),
    )
    item = shortfall_from_fills(paper.fills, policy=ArrivalPolicy.ARRIVAL_SNAPSHOT)
    payload = compare_paper(paper.tca, item)
    assert "paper_shortfall" in payload
    assert "tca_shortfall" in payload


def test_stressed_kind_is_not_observed() -> None:
    assert TCAKind.STRESSED.value == "stressed_tca"
    assert TCAKind.OBSERVED.value != TCAKind.STRESSED.value
    assert TCAKind.MODELLED.value != TCAKind.CALIBRATED.value


def test_uncertainty_unknown_band() -> None:
    assert interval(1.5, None) == "1.5 ± unknown"


def test_live_trading_gate_default() -> None:
    from quantlab.core.config import LiveSafetyGates

    assert LiveSafetyGates().live_trading is False
