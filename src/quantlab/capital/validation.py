"""Research-gate mapping for capital. Prompt 05 remains the only gate."""

from __future__ import annotations

from quantlab.capital.definitions import AbstentionCode, AllocationRequest, DecisionStatus
from quantlab.domain.research import CheckResult
from quantlab.research.gate import GateOutcome, ResearchGateResult


def map_gate(
    gate: ResearchGateResult | None,
    data_kind: str,
    *,
    allow_research_only_on_warn: bool,
    require_gate: bool = False,
) -> tuple[DecisionStatus, AbstentionCode, list[str]]:
    warnings: list[str] = []
    if data_kind not in {"real", "synthetic"}:
        return DecisionStatus.REJECTED, AbstentionCode.GATE_FAIL, ["unknown data kind"]
    synthetic = data_kind == "synthetic"
    if gate is None:
        if require_gate:
            return DecisionStatus.REJECTED, AbstentionCode.GATE_FAIL, ["research gate unavailable"]
        return DecisionStatus.RESEARCH_ONLY, AbstentionCode.NONE, ["research gate unavailable"]
    if gate.outcome in {GateOutcome.REJECT}:
        return DecisionStatus.REJECTED, AbstentionCode.GATE_FAIL, list(gate.warnings)
    if gate.outcome is GateOutcome.WARN:
        if allow_research_only_on_warn:
            return DecisionStatus.RESEARCH_ONLY, AbstentionCode.NONE, list(gate.warnings)
        return DecisionStatus.REJECTED, AbstentionCode.GATE_FAIL, list(gate.warnings)
    if synthetic:
        warnings.append("synthetic data cannot become production allocation")
        return DecisionStatus.RESEARCH_ONLY, AbstentionCode.NONE, warnings
    if gate.outcome in {GateOutcome.RESEARCH_CANDIDATE, GateOutcome.PROMOTED_TO_PAPER}:
        required = {
            "integrity", "pit_evidence", "next_bar_fill", "nonzero_costs", "test_set_sacred"
        }
        reasons = {reason.name: reason for reason in gate.reasons}
        if (
            len(reasons) != len(gate.reasons)
            or not required.issubset(reasons)
            or any(not reasons[name].required or reasons[name].result is not CheckResult.PASS
                   for name in required if name in reasons)
            or any(reason.result is not CheckResult.PASS for reason in gate.reasons
                   if reason.required)
            or any(reason.result in {CheckResult.FAIL, CheckResult.WARN}
                   for reason in gate.reasons)
        ):
            if not allow_research_only_on_warn:
                return (
                    DecisionStatus.REJECTED,
                    AbstentionCode.GATE_FAIL,
                    [*gate.warnings, "research-gate evidence is incomplete or inconsistent"],
                )
            return (
                DecisionStatus.RESEARCH_ONLY,
                AbstentionCode.NONE,
                [*gate.warnings, "research-gate evidence is incomplete or inconsistent"],
            )
        if gate.outcome is GateOutcome.PROMOTED_TO_PAPER:
            return (
                DecisionStatus.RESEARCH_ONLY,
                AbstentionCode.NONE,
                [*gate.warnings, "paper promotion requires a separate authorization"],
            )
    if gate.outcome is GateOutcome.RESEARCH_CANDIDATE:
        return DecisionStatus.ELIGIBLE, AbstentionCode.NONE, list(gate.warnings)
    return DecisionStatus.RESEARCH_ONLY, AbstentionCode.NONE, warnings


def cap_synthetic(status: DecisionStatus, data_kind: str) -> tuple[DecisionStatus, list[str]]:
    if data_kind != "synthetic":
        return status, []
    if status in {DecisionStatus.ELIGIBLE, DecisionStatus.ALLOCATED, DecisionStatus.PAPER_READY}:
        return DecisionStatus.RESEARCH_ONLY, ["synthetic cannot promote through Prompt 17"]
    return status, []


def override_cannot_bypass_gate(request: AllocationRequest) -> None:
    del request
