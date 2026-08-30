"""Paper execution policy. Reuses Prompt 13 scenario models; does not invent friction."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from quantlab.execution_research.definition import MarketMicrostructureDefinition
from quantlab.execution_research.scenarios import scenario_model
from quantlab.paper_oms.errors import OMSValidationError

POLICY_SCENARIOS: dict[str, str] = {
    "base": "BASE",
    "conservative": "CONSERVATIVE",
    "high_slippage": "HIGH_SLIPPAGE",
    "wide_spread": "WIDE_SPREAD",
    "high_impact": "HIGH_IMPACT",
    "low_liquidity": "LOW_LIQUIDITY",
    "high_latency": "HIGH_LATENCY",
    "partial_fill": "PARTIAL_FILL",
    "stressed": "STRESSED",
}


class PaperExecutionPolicy(BaseModel):
    model_config = ConfigDict(frozen=True)

    policy_id: str
    scenario_id: str
    model_id: str
    random_seed: int
    identity_hash: str
    unknown_liquidity: str = "unfilled"
    note: str = "Paper policy wrapping Prompt 13. Simulated fills are not broker prints."


def resolve_policy(policy_id: str = "base") -> PaperExecutionPolicy:
    key = policy_id.strip().lower() or "base"
    if key not in POLICY_SCENARIOS:
        raise OMSValidationError(f"unknown paper execution policy {policy_id}")
    definition = scenario_model(POLICY_SCENARIOS[key])
    return PaperExecutionPolicy(
        policy_id=key,
        scenario_id=POLICY_SCENARIOS[key],
        model_id=definition.definition_id,
        random_seed=definition.seed,
        identity_hash=definition.identity_hash(),
    )


def microstructure(policy: PaperExecutionPolicy) -> MarketMicrostructureDefinition:
    return scenario_model(policy.scenario_id)


def list_policies() -> list[PaperExecutionPolicy]:
    return [resolve_policy(item) for item in POLICY_SCENARIOS]
