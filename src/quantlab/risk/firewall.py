from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from quantlab.core.errors import RiskRejectedError
from quantlab.domain.models import (
    Instrument,
    ProposedPortfolio,
    RiskDecision,
    RiskVerdict,
    TargetPosition,
)
from quantlab.risk.states import RiskState, allows_new_exposure


@dataclass(frozen=True)
class DailyLossPolicy:
    """Owner-configured daily-loss ceiling; no default live limit is inferred."""

    max_loss_fraction: float
    max_age_seconds: float
    market_timezone: str

    def __post_init__(self) -> None:
        if (
            isinstance(self.max_loss_fraction, bool)
            or not math.isfinite(self.max_loss_fraction)
            or not 0 < self.max_loss_fraction <= 1
            or isinstance(self.max_age_seconds, bool)
            or not math.isfinite(self.max_age_seconds)
            or self.max_age_seconds < 0
        ):
            raise ValueError("daily-loss policy requires a finite positive limit and valid age")
        try:
            ZoneInfo(self.market_timezone)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise ValueError("daily-loss policy requires a valid market timezone") from exc


@dataclass(frozen=True)
class DailyLossEvidence:
    """Caller-supplied equity observations, not independently certified account data."""

    session_date: date
    opening_equity: float
    current_equity: float
    observed_at: datetime
    available_at: datetime
    source: str
    source_checksum: str
    cash_flow_adjusted: bool


class RiskLimits:
    def __init__(
        self,
        max_name_weight: float = 0.5,
        max_names: int = 10,
        max_gross: float = 1.0,
        allow_short: bool = False,
    ) -> None:
        if (
            isinstance(max_name_weight, bool)
            or not math.isfinite(max_name_weight)
            or max_name_weight < 0
        ):
            raise ValueError("max_name_weight must be finite and non-negative")
        if isinstance(max_names, bool) or not isinstance(max_names, int) or max_names < 0:
            raise ValueError("max_names must be a non-negative integer")
        if isinstance(max_gross, bool) or not math.isfinite(max_gross) or max_gross < 0:
            raise ValueError("max_gross must be finite and non-negative")
        if not isinstance(allow_short, bool):
            raise ValueError("allow_short must be a boolean")
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
        daily_loss_policy: DailyLossPolicy | None = None,
    ) -> None:
        self.limits = limits or RiskLimits()
        self.healthy = healthy
        self.state = state
        self.daily_loss_policy = daily_loss_policy
        self._listed: set[str] = set()

    def register_instruments(self, instruments: list[Instrument]) -> None:
        self._listed = {str(i.id) for i in instruments if i.listed}

    def authorize(
        self, proposal: ProposedPortfolio, *, daily_loss: DailyLossEvidence | None = None
    ) -> RiskDecision:
        if not self.healthy:
            return RiskDecision(verdict=RiskVerdict.REJECT, reasons=["risk_engine_unhealthy"])
        try:
            RiskLimits(
                max_name_weight=self.limits.max_name_weight,
                max_names=self.limits.max_names,
                max_gross=self.limits.max_gross,
                allow_short=self.limits.allow_short,
            )
        except (TypeError, ValueError):
            return RiskDecision(verdict=RiskVerdict.REJECT, reasons=["invalid_risk_limits"])
        if not allows_new_exposure(self.state):
            return RiskDecision(
                verdict=RiskVerdict.REJECT, reasons=[f"risk_state:{self.state.value}"]
            )

        if self.daily_loss_policy is not None:
            reason = _daily_loss_rejection(proposal.as_of, self.daily_loss_policy, daily_loss)
            if reason:
                return RiskDecision(verdict=RiskVerdict.REJECT, reasons=[reason])

        reasons: list[str] = []
        instruments = [str(target.instrument) for target in proposal.targets]
        if len(instruments) != len(set(instruments)):
            reasons.append("duplicate_instrument")
        if len(proposal.targets) > self.limits.max_names:
            reasons.append("too_many_names")
        if any(not math.isfinite(target.weight) for target in proposal.targets):
            reasons.append("nonfinite_weight")
        if reasons:
            return RiskDecision(verdict=RiskVerdict.REJECT, reasons=reasons)

        clipped: list[TargetPosition] = []
        for target in proposal.targets:
            if str(target.instrument) not in self._listed:
                reasons.append(f"unlisted:{target.instrument}")
                continue
            if target.weight < 0 and not self.limits.allow_short:
                reasons.append("short_not_allowed")
                continue
            weight = max(
                -self.limits.max_name_weight, min(target.weight, self.limits.max_name_weight)
            )
            if abs(weight - target.weight) > 1e-12:
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

    def require(
        self, proposal: ProposedPortfolio, *, daily_loss: DailyLossEvidence | None = None
    ) -> ProposedPortfolio:
        decision = self.authorize(proposal, daily_loss=daily_loss)
        if decision.verdict == RiskVerdict.REJECT or decision.modified is None:
            raise RiskRejectedError(";".join(decision.reasons) or "rejected")
        return decision.modified


def _daily_loss_rejection(
    as_of: datetime, policy: DailyLossPolicy, evidence: DailyLossEvidence | None
) -> str:
    if evidence is None:
        return "daily_loss_evidence_missing"
    if not isinstance(evidence, DailyLossEvidence):
        return "daily_loss_evidence_invalid"
    if (
        not isinstance(evidence.observed_at, datetime)
        or not isinstance(evidence.available_at, datetime)
        or as_of.utcoffset() is None
        or evidence.observed_at.utcoffset() is None
        or evidence.available_at.utcoffset() is None
        or evidence.observed_at > evidence.available_at
        or evidence.available_at > as_of
    ):
        return "daily_loss_evidence_time_invalid"
    if (as_of - evidence.observed_at).total_seconds() > policy.max_age_seconds:
        return "daily_loss_evidence_stale"
    timezone = ZoneInfo(policy.market_timezone)
    if (
        as_of.astimezone(timezone).date() != evidence.session_date
        or evidence.observed_at.astimezone(timezone).date() != evidence.session_date
    ):
        return "daily_loss_session_mismatch"
    if (
        not _finite_equity(evidence.opening_equity)
        or not _finite_equity(evidence.current_equity)
        or evidence.opening_equity <= 0
        or evidence.current_equity < 0
        or evidence.cash_flow_adjusted is not True
        or not isinstance(evidence.source, str)
        or not evidence.source.strip()
        or not isinstance(evidence.source_checksum, str)
        or len(evidence.source_checksum) != 64
        or any(char not in "0123456789abcdef" for char in evidence.source_checksum)
    ):
        return "daily_loss_evidence_invalid"
    loss_fraction = (evidence.opening_equity - evidence.current_equity) / evidence.opening_equity
    if not math.isfinite(loss_fraction):
        return "daily_loss_evidence_invalid"
    return "daily_loss_limit" if loss_fraction >= policy.max_loss_fraction else ""


def _finite_equity(value: object) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False
