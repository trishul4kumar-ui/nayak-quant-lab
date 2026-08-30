from __future__ import annotations

from quantlab.core.errors import RiskRejectedError
from quantlab.domain.models import (
    Instrument,
    ProposedPortfolio,
    RiskDecision,
    RiskVerdict,
    TargetPosition,
)
from quantlab.risk.states import RiskState, allows_new_exposure


class RiskLimits:
    def __init__(
        self,
        max_name_weight: float = 0.5,
        max_names: int = 10,
        max_gross: float = 1.0,
        allow_short: bool = False,
    ) -> None:
        self.max_name_weight = max_name_weight
        self.max_names = max_names
        self.max_gross = max_gross
        self.allow_short = allow_short


class RiskFirewall:
    """Mandatory authorize() before any OMS path. Fail closed."""

    def __init__(
        self,
        limits: RiskLimits | None = None,
        healthy: bool = True,
        state: RiskState = RiskState.NORMAL,
    ) -> None:
        self.limits = limits or RiskLimits()
        self.healthy = healthy
        self.state = state
        self._listed: set[str] = set()

    def register_instruments(self, instruments: list[Instrument]) -> None:
        self._listed = {str(i.id) for i in instruments if i.listed}

    def authorize(self, proposal: ProposedPortfolio) -> RiskDecision:
        if not self.healthy:
            return RiskDecision(verdict=RiskVerdict.REJECT, reasons=["risk_engine_unhealthy"])
        if not allows_new_exposure(self.state):
            return RiskDecision(
                verdict=RiskVerdict.REJECT, reasons=[f"risk_state:{self.state.value}"]
            )

        reasons: list[str] = []
        if len(proposal.targets) > self.limits.max_names:
            reasons.append("too_many_names")
        if proposal.gross_exposure > self.limits.max_gross + 1e-9:
            reasons.append("gross_exposure")

        clipped: list[TargetPosition] = []
        for target in proposal.targets:
            if str(target.instrument) not in self._listed:
                reasons.append(f"unlisted:{target.instrument}")
                continue
            if target.weight < 0 and not self.limits.allow_short:
                reasons.append("short_not_allowed")
                continue
            weight = min(target.weight, self.limits.max_name_weight)
            if weight + 1e-12 < target.weight:
                reasons.append(f"clipped:{target.instrument}")
            clipped.append(TargetPosition(instrument=target.instrument, weight=weight))

        if any(r.startswith("unlisted") or r == "short_not_allowed" for r in reasons):
            return RiskDecision(verdict=RiskVerdict.REJECT, reasons=reasons)

        modified = ProposedPortfolio(as_of=proposal.as_of, targets=clipped, reason=proposal.reason)
        if modified.gross_exposure > self.limits.max_gross + 1e-9:
            return RiskDecision(verdict=RiskVerdict.REJECT, reasons=["gross_after_clip"])

        if reasons:
            return RiskDecision(verdict=RiskVerdict.MODIFY, reasons=reasons, modified=modified)
        return RiskDecision(verdict=RiskVerdict.APPROVE, reasons=[], modified=modified)

    def require(self, proposal: ProposedPortfolio) -> ProposedPortfolio:
        decision = self.authorize(proposal)
        if decision.verdict == RiskVerdict.REJECT or decision.modified is None:
            raise RiskRejectedError(";".join(decision.reasons) or "rejected")
        return decision.modified
