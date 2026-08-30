"""Canonical hashes for capital policies and investment decisions."""

from __future__ import annotations

from typing import Any

from quantlab.backtest.spec import config_hash
from quantlab.capital.definitions import AllocationRequest, CapitalPolicy, InvestmentDecision


def policy_identity(policy: CapitalPolicy) -> str:
    return policy.config_hash or config_hash(
        policy.model_dump(mode="json", exclude={"config_hash", "created_at"})
    )


def request_identity(request: AllocationRequest) -> str:
    payload = request.model_dump(mode="json", exclude={"future_payload_ignored", "books"})
    if request.covariance is not None:
        payload["covariance_names"] = list(request.covariance.names)
        payload["covariance_as_of"] = str(request.covariance.as_of)
        payload["covariance_lookback"] = request.covariance.lookback
    return config_hash(payload)


def decision_payload(decision: InvestmentDecision) -> dict[str, Any]:
    return decision.model_dump(
        mode="json",
        exclude={"created_at", "decision_hash", "decision_id"},
    )


def hash_decision(decision: InvestmentDecision) -> str:
    return config_hash(decision_payload(decision))
