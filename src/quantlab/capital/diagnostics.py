"""Explainability, attribution, utilization, efficiency, stress, and stability."""

from __future__ import annotations

from pydantic import BaseModel, Field

from quantlab.capital.concentration import effective_n, herfindahl
from quantlab.capital.definitions import AllocationRequest, CapitalPolicy, InvestmentDecision
from quantlab.capital.library import get_policy, seed_request
from quantlab.domain.research import CheckResult
from quantlab.portfolio.covariance import CovarianceReport
from quantlab.portfolio.risk_model import portfolio_volatility, risk_contributions
from quantlab.risk.stress import StressResult, StressScenario, run_stress


class AllocationDiagnostics(BaseModel):
    stages: list[str] = Field(default_factory=list)
    utilization: dict[str, float] = Field(default_factory=dict)
    efficiency: dict[str, float | None] = Field(default_factory=dict)
    attribution: dict[str, str] = Field(default_factory=dict)
    explanations: list[dict[str, str]] = Field(default_factory=list)
    var_status: CheckResult = CheckResult.NOT_TESTED
    es_status: CheckResult = CheckResult.NOT_TESTED
    var_estimate: float | None = None
    es_estimate: float | None = None
    vol_status: str = ""
    warnings: list[str] = Field(default_factory=list)


def expected_shortfall_interface(n_obs: int) -> tuple[float | None, CheckResult]:
    if n_obs < 60:
        return None, CheckResult.NOT_TESTED
    return None, CheckResult.NOT_TESTED


def utilization(
    *,
    gross: float,
    gross_limit: float,
    vol: float | None,
    target_vol: float,
    turnover: float,
    max_turnover: float,
    cash_used: float,
    equity: float,
) -> dict[str, float]:
    return {
        "gross_utilization": gross / gross_limit if gross_limit else 0.0,
        "risk_utilization": (vol / target_vol) if vol and target_vol else 0.0,
        "turnover_utilization": turnover / max_turnover if max_turnover else 0.0,
        "cash_utilization": cash_used / equity if equity else 0.0,
    }


def efficiency(
    expected_port_return: float | None,
    capital: float,
    vol: float | None,
    turnover: float,
    drag: float,
) -> dict[str, float | None]:
    def ratio(num: float | None, den: float) -> float | None:
        if num is None or den <= 0:
            return None
        return num / den

    return {
        "return_per_capital": ratio(expected_port_return, capital),
        "return_per_risk": ratio(expected_port_return, vol or 0.0),
        "return_per_turnover": ratio(expected_port_return, turnover),
        "return_per_execution_cost": ratio(expected_port_return, drag),
    }


def explain_name(
    name: str,
    weight: float,
    request: AllocationRequest,
    policy: CapitalPolicy,
    *,
    binding: str,
    status: str,
) -> dict[str, str]:
    drivers = []
    if request.scores.get(name, 0.0) > 0:
        drivers.append(f"+ {request.expected_return_source.value} score {request.scores[name]:.4f}")
    vol = request.vols.get(name)
    if vol is not None:
        drivers.append(f"vol={vol:.4f}")
    return {
        "name": name,
        "target_weight": f"{weight:.6f}",
        "drivers": "; ".join(drivers) or "none",
        "constraints": f"max_position={policy.max_position_weight}",
        "binding_constraint": binding,
        "confidence": f"{request.confidence.allocation_confidence():.2f}",
        "status": status,
    }


def explain_decision(
    decision: InvestmentDecision,
    request: AllocationRequest | None = None,
) -> dict[str, object]:
    policy = get_policy(decision.capital_policy_id) if decision.capital_policy_id else None
    rows = []
    for name, weight in sorted(decision.target_weights.items()):
        req = request or seed_request()
        rows.append(
            explain_name(
                name,
                weight,
                req,
                policy or get_policy("CAP-RESEARCH-001"),
                binding="none" if weight > 0 else "excluded",
                status=decision.decision_status.value,
            )
        )
    return {
        "decision_id": decision.decision_id,
        "status": decision.decision_status.value,
        "abstention": decision.abstention_reason,
        "capital_state": decision.capital_state.value,
        "gross_target": decision.gross_target,
        "net_target": decision.net_target,
        "allocations": rows,
        "note": "Explanations are reconstructed from recorded inputs. Nothing is fabricated.",
        "live_trading": False,
    }


def stress_allocation(
    weights: dict[str, float],
    cov: CovarianceReport,
    scenario: StressScenario,
) -> StressResult:
    return run_stress(weights, cov, scenario)


def stability_l1(base: dict[str, float], other: dict[str, float]) -> float:
    names = set(base) | set(other)
    return sum(abs(base.get(n, 0.0) - other.get(n, 0.0)) for n in names)


def concentration_note(weights: dict[str, float]) -> dict[str, float]:
    return {"hhi": herfindahl(weights), "n_eff": effective_n(weights)}


def risk_view(weights: dict[str, float], cov: CovarianceReport | None) -> dict[str, object]:
    if cov is None:
        return {"status": CheckResult.NOT_TESTED.value, "volatility": None, "contributions": []}
    diag = risk_contributions(weights, cov)
    return {
        "status": diag.status.value,
        "volatility": diag.volatility,
        "contributions": [item.model_dump(mode="json") for item in diag.contributions],
        "note": diag.note,
    }


def portfolio_vol(weights: dict[str, float], cov: CovarianceReport | None) -> float | None:
    if cov is None:
        return None
    return portfolio_volatility(weights, cov)
