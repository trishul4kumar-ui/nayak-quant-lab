"""Broker-neutral account-state protocol. No broker connector."""

from __future__ import annotations

from typing import Protocol

from quantlab.safety.gate_results import GateId, GateResult, GateVerdict
from quantlab.safety.models import SafetyRequest


class AccountStateProvider(Protocol):
    def account_hash(self) -> str: ...


class PositionStateProvider(Protocol):
    def position_hash(self) -> str: ...


class BalanceStateProvider(Protocol):
    def balance_hash(self) -> str: ...


class OrderStateProvider(Protocol):
    def order_hash(self) -> str: ...


class FillStateProvider(Protocol):
    def fill_hash(self) -> str: ...


def check_account(request: SafetyRequest) -> GateResult:
    if request.future_account:
        return GateResult(
            gate_id=GateId.G5_ACCOUNT_STATE,
            verdict=GateVerdict.BLOCK,
            reason="future account state",
        )
    if not request.account_state_hash:
        return GateResult(
            gate_id=GateId.G5_ACCOUNT_STATE,
            verdict=GateVerdict.NOT_TESTED,
            reason="broker-neutral account evidence missing",
        )
    return GateResult(
        gate_id=GateId.G5_ACCOUNT_STATE,
        verdict=GateVerdict.PASS,
        reason="account evidence reference present (not broker-confirmed)",
        critical=False,
    )
