"""Research-gate mapping for capital. Prompt 05 remains the only gate."""

from __future__ import annotations

from quantlab.capital.definitions import AbstentionCode, AllocationRequest, DecisionStatus
from quantlab.research.gate import GateOutcome, ResearchGateResult


def map_gate(
    gate: ResearchGateResult | None,
    data_kind: str,
    *,
    allow_research_only_on_warn: bool,
) -> tuple[DecisionStatus, AbstentionCode, list[str]]:
    warnings: list[str] = []
    synthetic = data_kind == "synthetic"
    if gate is None:
        status = DecisionStatus.RESEARCH_ONLY if synthetic else DecisionStatus.ELIGIBLE
        return status, AbstentionCode.NONE, warnings
    if gate.outcome in {GateOutcome.REJECT}:
        return DecisionStatus.REJECTED, AbstentionCode.GATE_FAIL, list(gate.warnings)
    if gate.outcome is GateOutcome.WARN:
        if allow_research_only_on_warn:
            return DecisionStatus.RESEARCH_ONLY, AbstentionCode.NONE, list(gate.warnings)
        return DecisionStatus.REJECTED, AbstentionCode.GATE_FAIL, list(gate.warnings)
    if synthetic:
        warnings.append("synthetic data cannot become production allocation")
        return DecisionStatus.RESEARCH_ONLY, AbstentionCode.NONE, warnings
    if gate.outcome is GateOutcome.RESEARCH_CANDIDATE:
        return DecisionStatus.ELIGIBLE, AbstentionCode.NONE, list(gate.warnings)
    if gate.outcome is GateOutcome.PROMOTED_TO_PAPER:
        return DecisionStatus.PAPER_READY, AbstentionCode.NONE, list(gate.warnings)
    return DecisionStatus.RESEARCH_ONLY, AbstentionCode.NONE, warnings


def cap_synthetic(status: DecisionStatus, data_kind: str) -> tuple[DecisionStatus, list[str]]:
    if data_kind != "synthetic":
        return status, []
    if status in {DecisionStatus.ELIGIBLE, DecisionStatus.ALLOCATED, DecisionStatus.PAPER_READY}:
        return DecisionStatus.RESEARCH_ONLY, ["synthetic cannot promote through Prompt 17"]
    return status, []


def override_cannot_bypass_gate(request: AllocationRequest) -> None:
    del request
