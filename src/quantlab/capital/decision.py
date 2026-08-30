"""Immutable investment decisions. Historical records are never mutated."""

from __future__ import annotations

from quantlab.capital.definitions import InvestmentDecision, TargetPortfolio
from quantlab.capital.errors import CapitalError
from quantlab.capital.identity import hash_decision
from quantlab.core.errors import InfeasibleCapitalAllocation


def freeze_decision(decision: InvestmentDecision) -> InvestmentDecision:
    hashed = hash_decision(decision)
    return decision.model_copy(
        update={"decision_hash": hashed, "decision_id": f"DEC-{hashed[:12]}"}
    )


def mutate_decision(decision: InvestmentDecision, **_updates: object) -> None:
    del decision
    raise CapitalError(
        "decision_mutation: historical decisions cannot be mutated; create a new decision"
    )


def mutate_policy(*_args: object, **_kwargs: object) -> None:
    raise CapitalError("capital_policy_mutation: policies are immutable after hash")


def mutate_target(target: TargetPortfolio, **_updates: object) -> None:
    del target
    raise CapitalError("target portfolios are immutable; create a new target")


def infeasible_from_exception(exc: InfeasibleCapitalAllocation) -> InfeasibleCapitalAllocation:
    return exc
