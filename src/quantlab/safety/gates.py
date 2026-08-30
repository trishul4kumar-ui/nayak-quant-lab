"""G0–G15 evaluation. BLOCK / EMERGENCY / critical NOT_TESTED prevent release."""

from __future__ import annotations

from quantlab.core.config import LiveSafetyGates
from quantlab.safety.account_checks import check_account
from quantlab.safety.emergency import check_emergency
from quantlab.safety.gate_results import GateId, GateResult, GateVerdict
from quantlab.safety.human_authorization import check_human
from quantlab.safety.idempotency import check_idempotency
from quantlab.safety.kill_switch import live_release_blocked
from quantlab.safety.market_checks import check_market
from quantlab.safety.models import SafetyRequest
from quantlab.safety.order_checks import check_order
from quantlab.safety.reconciliation import check_reconciliation
from quantlab.safety.risk_checks import check_risk
from quantlab.safety.staleness import check_staleness
from quantlab.safety.state import SafetyState, current


def _g0(request: SafetyRequest) -> GateResult:
    gates = LiveSafetyGates()
    if request.live_release or gates.live_trading:
        return GateResult(
            gate_id=GateId.G0_LIVE_MODE,
            verdict=GateVerdict.BLOCK,
            reason="LIVE_TRADING=false cannot authorize live release",
        )
    return GateResult(
        gate_id=GateId.G0_LIVE_MODE,
        verdict=GateVerdict.PASS,
        reason="live mode off; research/paper/shadow evaluation only",
    )


def _g1(request: SafetyRequest) -> GateResult:
    if request.research_gate_failed:
        return GateResult(
            gate_id=GateId.G1_RESEARCH_INTEGRITY,
            verdict=GateVerdict.BLOCK,
            reason="failed research gate",
        )
    return GateResult(
        gate_id=GateId.G1_RESEARCH_INTEGRITY,
        verdict=GateVerdict.NOT_TESTED,
        reason="research integrity not attached to this request",
        critical=False,
    )


def _g2(request: SafetyRequest) -> GateResult:
    if request.certification_expired:
        return GateResult(
            gate_id=GateId.G2_CERTIFICATION,
            verdict=GateVerdict.BLOCK,
            reason="expired certification",
        )
    if not request.certification_id:
        return GateResult(
            gate_id=GateId.G2_CERTIFICATION,
            verdict=GateVerdict.NOT_TESTED,
            reason="missing certification",
        )
    if request.certification_state and request.certification_state != "certified":
        return GateResult(
            gate_id=GateId.G2_CERTIFICATION,
            verdict=GateVerdict.BLOCK,
            reason="certification mismatch",
        )
    return GateResult(
        gate_id=GateId.G2_CERTIFICATION,
        verdict=GateVerdict.PASS,
        reason="certification reference present; CERTIFIED is not live",
    )


def _g3(request: SafetyRequest) -> GateResult:
    if not request.shadow_cycle_id and not request.paper_evidence_id:
        return GateResult(
            gate_id=GateId.G3_SHADOW_EVIDENCE,
            verdict=GateVerdict.NOT_TESTED,
            reason="missing shadow/paper evidence",
        )
    return GateResult(
        gate_id=GateId.G3_SHADOW_EVIDENCE,
        verdict=GateVerdict.PASS,
        reason="shadow/paper evidence referenced (not broker)",
        critical=False,
    )


def _g10() -> GateResult:
    if live_release_blocked():
        return GateResult(
            gate_id=GateId.G10_KILL_SWITCH,
            verdict=GateVerdict.BLOCK,
            reason="LIVE_RELEASE_KILL or GLOBAL_KILL active",
        )
    return GateResult(
        gate_id=GateId.G10_KILL_SWITCH,
        verdict=GateVerdict.PASS,
        reason="no live-release kill (still not live)",
    )


def _g13(request: SafetyRequest) -> GateResult:
    if request.ai_override:
        return GateResult(
            gate_id=GateId.G13_AI_BOUNDARY,
            verdict=GateVerdict.BLOCK,
            reason="AI cannot override safety",
        )
    return GateResult(
        gate_id=GateId.G13_AI_BOUNDARY,
        verdict=GateVerdict.PASS,
        reason="no AI override",
        critical=False,
    )


def _g15() -> GateResult:
    return GateResult(
        gate_id=GateId.G15_FINAL_RELEASE,
        verdict=GateVerdict.BLOCK,
        reason="G15 final release BLOCK while LIVE_TRADING=false",
    )


def evaluate_gates(request: SafetyRequest) -> tuple[GateResult, ...]:
    rows = [
        _g0(request),
        _g1(request),
        _g2(request),
        _g3(request),
        check_market(request),
        check_account(request),
        check_risk(request),
        check_order(request),
        check_staleness(request),
        check_reconciliation(request),
        _g10(),
        check_idempotency(request),
        check_human(request),
        _g13(request),
        check_emergency(),
        _g15(),
    ]
    if current() in {SafetyState.HALTED, SafetyState.DISABLED}:
        rows.append(
            GateResult(
                gate_id=GateId.G15_FINAL_RELEASE,
                verdict=GateVerdict.BLOCK,
                reason=f"state {current().value} cannot release",
            )
        )
    return tuple(rows)
