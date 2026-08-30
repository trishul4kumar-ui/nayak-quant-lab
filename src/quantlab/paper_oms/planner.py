"""Order intents → deterministic paper plan. Does not silently resize the target."""

from __future__ import annotations

from datetime import datetime, timedelta

from quantlab.execution_research.definition import LatencyKind
from quantlab.paper_oms.enums import FillPolicy, PaperOrderType, TimeInForce
from quantlab.paper_oms.identity import hash_intents, hash_plan
from quantlab.paper_oms.models import (
    OrderIntent,
    OrderPlan,
    PaperAccount,
    PaperMarketSnapshot,
    PlannedInstruction,
)
from quantlab.paper_oms.policy import PaperExecutionPolicy, microstructure


def _arrival(
    intent: OrderIntent, latency_sessions: int, latency_zero: bool
) -> tuple[datetime, int]:
    delay = 0 if latency_zero else max(int(latency_sessions), 0)
    arrival = intent.as_of + timedelta(days=delay)
    return arrival, delay


def plan_orders(
    intents: list[OrderIntent],
    account: PaperAccount,
    snapshot: PaperMarketSnapshot,
    policy: PaperExecutionPolicy,
) -> OrderPlan:
    del account
    definition = microstructure(policy)
    latency_zero = definition.latency_model is LatencyKind.ZERO
    fill_policy = FillPolicy.SIMULATED
    if definition.fill_model.value == "full":
        fill_policy = FillPolicy.FULL
    elif definition.fill_model.value == "ratio_capped":
        fill_policy = FillPolicy.RATIO_CAPPED
    elif definition.fill_model.value == "participation_capped":
        fill_policy = FillPolicy.PARTICIPATION_CAPPED
    instructions: list[PlannedInstruction] = []
    residuals: dict[str, float] = {}
    for intent in intents:
        arrival, _delay = _arrival(intent, definition.latency_sessions, latency_zero)
        instructions.append(
            PlannedInstruction(
                security_id=intent.security_id,
                side=intent.side,
                action=intent.action,
                quantity=intent.rounded_quantity,
                requested_quantity=intent.requested_quantity,
                rounded_quantity=intent.rounded_quantity,
                residual_quantity=intent.residual_quantity,
                residual_notional=intent.residual_notional,
                rounding_policy=intent.rounding_policy,
                order_type=PaperOrderType.MARKET,
                limit_price=None,
                reference_price=intent.reference_price,
                time_in_force=TimeInForce.DAY,
                expected_arrival=arrival,
                expected_fill_policy=fill_policy,
                intent_id=intent.intent_id,
                intent_hash=intent.intent_hash,
            )
        )
        if intent.residual_quantity > 0:
            residuals[intent.security_id] = intent.residual_quantity
    intent_hash = hash_intents(intents)
    decision_hash = intents[0].decision_hash if intents else ""
    plan = OrderPlan(
        order_plan_id="",
        decision_hash=decision_hash,
        intent_hash=intent_hash,
        snapshot_id=snapshot.snapshot_id,
        planning_time=snapshot.as_of,
        execution_policy_id=policy.policy_id,
        instructions=instructions,
        residuals=residuals,
    )
    hashed = hash_plan(plan)
    return plan.model_copy(
        update={"order_plan_hash": hashed, "order_plan_id": f"PLAN-{hashed[:12]}"}
    )
