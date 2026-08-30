"""Order-identity safety. Does not place or clip live orders."""

from __future__ import annotations

from quantlab.safety.gate_results import GateId, GateResult, GateVerdict
from quantlab.safety.models import SafetyRequest

_SIDES = {"buy", "sell"}
_TYPES = {"limit", "market"}


def check_order(request: SafetyRequest) -> GateResult:
    if request.quantity < 0:
        return GateResult(
            gate_id=GateId.G7_ORDER_SAFETY,
            verdict=GateVerdict.BLOCK,
            reason="negative quantity",
        )
    if request.side not in _SIDES:
        return GateResult(
            gate_id=GateId.G7_ORDER_SAFETY,
            verdict=GateVerdict.BLOCK,
            reason="invalid side",
        )
    if not request.symbol or not request.security_id:
        return GateResult(
            gate_id=GateId.G7_ORDER_SAFETY,
            verdict=GateVerdict.BLOCK,
            reason="unknown security",
        )
    if request.price < 0:
        return GateResult(
            gate_id=GateId.G7_ORDER_SAFETY,
            verdict=GateVerdict.BLOCK,
            reason="invalid price",
        )
    if request.order_type not in _TYPES:
        return GateResult(
            gate_id=GateId.G7_ORDER_SAFETY,
            verdict=GateVerdict.BLOCK,
            reason="unauthorized order type",
        )
    if request.mutated_target or request.mutated_decision or request.mutated_order_plan:
        return GateResult(
            gate_id=GateId.G7_ORDER_SAFETY,
            verdict=GateVerdict.BLOCK,
            reason="mutated decision/target/plan",
        )
    return GateResult(
        gate_id=GateId.G7_ORDER_SAFETY,
        verdict=GateVerdict.PASS,
        reason="order fields internally consistent",
        critical=False,
    )
