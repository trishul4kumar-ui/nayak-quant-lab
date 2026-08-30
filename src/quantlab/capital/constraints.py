"""Hard capital constraints. Never silently relaxed, clipped, or fallback-sized."""

from __future__ import annotations

from quantlab.capital.budgets import account_gross, account_net
from quantlab.capital.concentration import herfindahl, max_name_weight, top_k_weight
from quantlab.capital.definitions import (
    CapitalBooks,
    CapitalPolicy,
    ConstraintCheck,
)
from quantlab.capital.errors import CapitalError, InfeasibleCapitalAllocation
from quantlab.capital.turnover import estimate_turnover
from quantlab.domain.research import CheckResult


def evaluate_constraints(
    weights: dict[str, float],
    policy: CapitalPolicy,
    books: CapitalBooks,
    investable: float,
    previous: dict[str, float],
    *,
    beta: float | None,
    beta_status: CheckResult,
    factor: float | None,
    factor_status: CheckResult,
    sector_status: CheckResult = CheckResult.NOT_TESTED,
    shortability_status: CheckResult = CheckResult.NOT_TESTED,
) -> list[ConstraintCheck]:
    checks: list[ConstraintCheck] = []
    gross = account_gross(weights, books, investable)
    net = account_net(weights, books, investable)
    max_w = max_name_weight(weights)
    turnover = estimate_turnover(previous, weights)
    hhi = herfindahl(weights)
    top5 = top_k_weight(weights, 5)
    top10 = top_k_weight(weights, 10)

    def add(name: str, value: float, bound: float, ok: bool, note: str) -> None:
        checks.append(
            ConstraintCheck(
                name=name,
                result=CheckResult.PASS if ok else CheckResult.FAIL,
                bound=bound,
                value=value,
                note=note,
            )
        )

    add(
        "max_position_weight",
        max_w,
        policy.max_position_weight,
        max_w <= policy.max_position_weight + 1e-9,
        "single-name weight of investable capital",
    )
    add(
        "gross_leverage_limit",
        gross,
        policy.gross_leverage_limit,
        gross <= policy.gross_leverage_limit + 1e-9,
        "sum |notional| / equity",
    )
    add(
        "net_exposure_limit",
        abs(net),
        policy.net_exposure_limit,
        abs(net) <= policy.net_exposure_limit + 1e-9,
        "signed notional / equity",
    )
    add("max_hhi", hhi, policy.max_hhi, hhi <= policy.max_hhi + 1e-9, "HHI = Σ w²")
    add(
        "max_top_5_weight",
        top5,
        policy.max_top_5_weight,
        top5 <= policy.max_top_5_weight + 1e-9,
        "sum of five largest |w|",
    )
    add(
        "max_top_10_weight",
        top10,
        policy.max_top_10_weight,
        top10 <= policy.max_top_10_weight + 1e-9,
        "sum of ten largest |w|",
    )
    if policy.constraint_policy.turnover_hard:
        add(
            "max_turnover",
            turnover,
            policy.max_turnover,
            turnover <= policy.max_turnover + 1e-9,
            "0.5 × L1 vs previous target",
        )
    else:
        checks.append(
            ConstraintCheck(
                name="max_turnover",
                result=CheckResult.WARN if turnover > policy.max_turnover else CheckResult.PASS,
                bound=policy.max_turnover,
                value=turnover,
                note="soft turnover",
            )
        )
    if policy.max_beta is not None or policy.min_beta is not None:
        if beta_status is CheckResult.NOT_TESTED or beta is None:
            checks.append(
                ConstraintCheck(
                    name="beta_limit",
                    result=CheckResult.NOT_TESTED,
                    note="beta missing; not substituted with zero",
                )
            )
        else:
            lo = policy.min_beta if policy.min_beta is not None else float("-inf")
            hi = policy.max_beta if policy.max_beta is not None else float("inf")
            add("beta_limit", beta, hi, lo - 1e-9 <= beta <= hi + 1e-9, "B_p = Σ w_i B_i")
    if policy.max_factor_exposure is not None or policy.min_factor_exposure is not None:
        if factor_status is CheckResult.NOT_TESTED or factor is None:
            checks.append(
                ConstraintCheck(
                    name="factor_limit",
                    result=CheckResult.NOT_TESTED,
                    note="factor exposure missing; not substituted with zero",
                )
            )
        else:
            lo = (
                policy.min_factor_exposure
                if policy.min_factor_exposure is not None
                else float("-inf")
            )
            hi = (
                policy.max_factor_exposure
                if policy.max_factor_exposure is not None
                else float("inf")
            )
            add("factor_limit", factor, hi, lo - 1e-9 <= factor <= hi + 1e-9, "factor budget")
    checks.append(
        ConstraintCheck(
            name="sector_constraint",
            result=sector_status,
            note="PIT sector data is not fabricated",
        )
    )
    checks.append(
        ConstraintCheck(
            name="shortability",
            result=shortability_status,
            note="unknown shortability is NOT_TESTED",
        )
    )
    return checks


def enforce_hard(checks: list[ConstraintCheck], weights: dict[str, float]) -> None:
    failed = [item.name for item in checks if item.result is CheckResult.FAIL]
    if not failed:
        return
    raise InfeasibleCapitalAllocation(
        "hard capital constraints cannot be satisfied",
        violated_constraints=failed,
        required_adjustment="change policy or candidate; constraints were not relaxed",
        current_candidate=dict(weights),
        feasibility_diagnostics={item.name: item.result.value for item in checks},
    )


def refuse_silent_fallback(policy: CapitalPolicy) -> None:
    if policy.constraint_policy.fallback_sizing:
        return
    raise CapitalError("silent_fallback is prohibited unless the policy names an explicit fallback")
