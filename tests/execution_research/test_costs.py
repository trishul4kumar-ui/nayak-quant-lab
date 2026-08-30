from __future__ import annotations

from datetime import UTC, datetime

from quantlab.domain.models import Side
from quantlab.execution_research.attribution import cost_attribution
from quantlab.execution_research.costs import cost_components, explicit_bps
from quantlab.execution_research.definition import OrderIntent
from quantlab.execution_research.fills import simulate_fill
from quantlab.execution_research.registry import get_execution_model
from quantlab.execution_research.simulator import SimulationResult


def test_explicit_legs_do_not_invent_india_fees() -> None:
    model = get_execution_model("exec_base")
    assert explicit_bps(model.cost) == 10.0
    names = {row.name: row for row in cost_components(model.cost)}
    assert names["stt_bps"].status.value == "unspecified"
    assert names["stt_bps"].value == 0.0


def test_cost_components_sum_to_total() -> None:
    as_of = datetime(2024, 1, 2, tzinfo=UTC)
    fill = simulate_fill(
        OrderIntent(
            intent_id="c",
            decision_time=as_of,
            security_id="NSE:TCS",
            side=Side.BUY,
            target_quantity=100.0,
            reference_price=100.0,
            max_participation=1.0,
        ),
        get_execution_model("exec_base"),
        arrival_time=as_of,
        arrival_price=100.0,
        volume=1_000_000.0,
        trailing_volume=1_000_000.0,
        trailing_vol=0.01,
    )
    summed = fill.spread_cost + fill.slippage_cost + fill.impact_cost + fill.explicit_cost
    assert abs(fill.total_cost - summed) < 1e-9
    assert fill.total_cost > 0
    sim = SimulationResult(
        model_id="exec_base",
        identity_hash="x",
        fills=[fill],
        total_cost=fill.total_cost,
        spread_cost=fill.spread_cost,
        slippage_cost=fill.slippage_cost,
        impact_cost=fill.impact_cost,
        explicit_cost=fill.explicit_cost,
    )
    attr = cost_attribution(sim)
    assert abs(attr.total - fill.total_cost) < 1e-9
