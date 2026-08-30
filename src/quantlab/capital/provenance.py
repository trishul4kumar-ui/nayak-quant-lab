"""Allocation provenance bundle. Links research identity without owning the gate."""

from __future__ import annotations

from pydantic import BaseModel, Field

from quantlab.capital.definitions import AllocationRequest, CapitalPolicy


class AllocationProvenance(BaseModel):
    snapshot_id: str
    dataset_checksum: str
    portfolio_spec_id: str
    alpha_version: str
    model_version: str = ""
    ensemble_id: str = ""
    risk_model_version: str
    covariance_version: str
    regime_version: str
    execution_model_version: str
    capital_policy_id: str
    capital_policy_hash: str
    knowledge_snapshot_id: str
    software_version: str
    request_hash: str = ""
    identifiers: dict[str, str] = Field(default_factory=dict)


def bundle(
    request: AllocationRequest,
    policy: CapitalPolicy,
    *,
    software_version: str,
    request_hash: str,
) -> AllocationProvenance:
    return AllocationProvenance(
        snapshot_id=request.snapshot_id,
        dataset_checksum=request.dataset_checksum,
        portfolio_spec_id=request.portfolio_spec_id,
        alpha_version=request.input_alpha_version,
        ensemble_id=request.ensemble_id,
        risk_model_version=request.risk_model_version,
        covariance_version=request.covariance_version,
        regime_version=request.regime_version,
        execution_model_version=request.execution_model_version,
        capital_policy_id=policy.policy_id,
        capital_policy_hash=policy.config_hash,
        knowledge_snapshot_id=request.knowledge_snapshot_id,
        software_version=software_version,
        request_hash=request_hash,
        identifiers={
            "experiment_id": request.experiment_id,
            "research_result_id": request.research_result_id,
            "strategy_id": request.strategy_id,
        },
    )
