"""Paper execution adapter. Consumes Prompt 13 simulate_fill. No live broker."""

from __future__ import annotations

from typing import Protocol

from quantlab.execution_research.definition import ExecutionLeakFlags
from quantlab.execution_research.definition import OrderIntent as ResearchIntent
from quantlab.execution_research.fills import simulate_fill
from quantlab.paper_oms.enums import LiquidityMark
from quantlab.paper_oms.errors import PaperSafetyError
from quantlab.paper_oms.identity import hash_fill
from quantlab.paper_oms.models import PaperFill, PaperMarketSnapshot, PaperOrder
from quantlab.paper_oms.policy import PaperExecutionPolicy, microstructure
from quantlab.paper_oms.safety import assert_paper_only


class BrokerAdapter(Protocol):
    """Future-neutral contract. Prompt 18 must not instantiate a live adapter."""

    def submit(self, order: PaperOrder) -> PaperOrder: ...


class PaperExecutionAdapter:
    """The only adapter Prompt 18 may use."""

    def __init__(self, policy: PaperExecutionPolicy) -> None:
        self.policy = policy
        self.definition = microstructure(policy)

    def submit(self, order: PaperOrder) -> PaperOrder:
        raise PaperSafetyError("PaperExecutionAdapter does not place broker orders")

    def simulate(
        self,
        order: PaperOrder,
        snapshot: PaperMarketSnapshot,
        *,
        leaks: ExecutionLeakFlags | None = None,
    ) -> PaperFill:
        assert_paper_only()
        flags = leaks or ExecutionLeakFlags()
        volume = snapshot.volumes.get(order.security_id)
        if volume is None and self.policy.unknown_liquidity == "unfilled":
            volume = None
        research = ResearchIntent(
            intent_id=order.order_id,
            decision_time=order.created_at,
            security_id=order.security_id,
            side=order.side,
            target_quantity=order.rounded_quantity,
            reference_price=order.reference_price,
            max_participation=self.definition.max_participation,
        )
        arrival_price = snapshot.prices.get(order.security_id, order.reference_price)
        simulated = simulate_fill(
            research,
            self.definition,
            arrival_time=order.arrival_time,
            arrival_price=arrival_price,
            volume=volume,
            trailing_volume=volume,
            trailing_vol=None,
            leaks=flags,
        )
        if volume is None:
            liquidity = LiquidityMark.UNKNOWN
        elif simulated.quantity <= 0:
            liquidity = LiquidityMark.UNFILLED
        else:
            liquidity = LiquidityMark.KNOWN
        taxes_status_unspecified = 0.0
        fill = PaperFill(
            fill_id="",
            order_id=order.order_id,
            security_id=order.security_id,
            side=order.side,
            requested_quantity=order.rounded_quantity,
            filled_quantity=simulated.quantity,
            remaining_quantity=simulated.remaining_quantity,
            reference_price=order.reference_price,
            arrival_price=arrival_price,
            execution_price=simulated.execution_price,
            gross_notional=simulated.quantity * simulated.execution_price,
            commission=simulated.explicit_cost,
            taxes=taxes_status_unspecified,
            fees=simulated.explicit_cost,
            spread_cost=simulated.spread_cost,
            slippage_cost=simulated.slippage_cost,
            impact_cost=simulated.impact_cost,
            total_cost=simulated.total_cost,
            arrival_time=order.arrival_time,
            fill_time=simulated.timestamp,
            latency_sessions=self.definition.latency_sessions,
            liquidity_status=liquidity,
            execution_model_id=self.definition.definition_id,
        )
        hashed = hash_fill(fill)
        return fill.model_copy(update={"fill_hash": hashed, "fill_id": f"PF-{hashed[:12]}"})


def assert_not_live_adapter(adapter: object) -> None:
    if type(adapter).__name__ != "PaperExecutionAdapter":
        raise PaperSafetyError("paper OMS may only use PaperExecutionAdapter")
