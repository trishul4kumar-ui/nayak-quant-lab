"""Stability of adaptive weights and efficacy. Flags are research warnings."""

from __future__ import annotations

from quantlab.adaptive.state import AdaptiveModelState, StabilityReport
from quantlab.domain.research import CheckResult


def assess_stability(
    state: AdaptiveModelState, weights_path: list[dict[str, float]]
) -> StabilityReport:
    flags: list[str] = []
    ics = state.ic_history
    n_sign = 0
    for i in range(1, len(ics)):
        if (ics[i] > 0) != (ics[i - 1] > 0):
            n_sign += 1
    osc = None if len(ics) < 2 else n_sign / (len(ics) - 1)
    if osc is not None and osc > 0.45:
        flags.append("rapid_oscillation")
    if n_sign >= max(len(ics) - 1, 1) and len(ics) >= 8:
        flags.append("sign_instability")
    last_hhi = None
    if weights_path:
        last = weights_path[-1]
        last_hhi = sum(v * v for v in last.values())
        if last_hhi >= 0.8 and len(last) > 1:
            flags.append("weight_concentration")
        if any(abs(v) > 1.0 + 1e-9 for v in last.values()):
            flags.append("parameter_explosion")
    if state.n_updates < 8:
        flags.append("insufficient_history")
    status = CheckResult.WARN if flags else CheckResult.PASS
    return StabilityReport(
        n_sign_changes=n_sign,
        weight_hhi=last_hhi,
        oscillation_rate=osc,
        flags=flags,
        status=status,
    )
