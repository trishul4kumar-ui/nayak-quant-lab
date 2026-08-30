"""Frozen research specifications and plans. Mutation creates a new version."""

from __future__ import annotations

from pydantic import BaseModel, Field

from quantlab.backtest.spec import config_hash
from quantlab.orchestration.contracts import (
    ExperimentType,
    MetricRole,
    SelectionPolicy,
    StoppingPolicy,
)
from quantlab.orchestration.errors import OrchestrationError


class MetricSpec(BaseModel):
    name: str
    role: MetricRole = MetricRole.DIAGNOSTIC


class ResearchSpec(BaseModel):
    experiment_id: str
    experiment_version: str = "1"
    hypothesis_id: str
    hypothesis_version: str = "1"
    family_id: str
    experiment_type: ExperimentType = ExperimentType.DISCOVERY
    dataset_id: str = "synthetic_nse"
    snapshot_id: str = ""
    universe: list[str] = Field(default_factory=list)
    feature_ids: list[str] = Field(default_factory=lambda: ["momentum_20"])
    label_id: str = "next_bar_close_return"
    alpha_id: str = "rank_momentum_20"
    model_id: str = ""
    ensemble_id: str = "mom20"
    portfolio_id: str = "mom20_topn"
    risk_model_id: str = "sample_cs"
    execution_model_id: str = "exec_base"
    validation_protocol: str = "next_bar_cost_adjusted"
    multiple_testing_family: str = ""
    multiple_testing_method: str = "benjamini_hochberg"
    seed: int = 0
    lookback: int = 20
    top_n: int = 2
    cost_bps: float = 10.0
    n_days: int = 80
    baseline_id: str = "equal_weight"
    parent_experiment: str = ""
    search_space_id: str = "mom_lookback_cost"
    selection_policy: SelectionPolicy = SelectionPolicy.PRE_REGISTERED
    stopping_policy: StoppingPolicy = StoppingPolicy.PRE_REGISTERED_BUDGET
    primary_metric: str = "total_return"
    metrics: list[MetricSpec] = Field(
        default_factory=lambda: [
            MetricSpec(name="total_return", role=MetricRole.PRIMARY),
            MetricSpec(name="sharpe", role=MetricRole.SECONDARY),
            MetricSpec(name="max_drawdown", role=MetricRole.DIAGNOSTIC),
        ]
    )

    def identity_hash(self) -> str:
        return config_hash(self.model_dump(mode="json"))

    def config_hash(self) -> str:
        return self.identity_hash()


class ResearchPlan(BaseModel):
    plan_id: str
    spec: ResearchSpec
    budget_max_candidates: int = 8
    budget_max_experiments: int = 16
    replication_policy: str = "same_spec_same_snapshot"
    notes: str = "Plan is frozen before execution. Changing it creates a new version."

    def identity_hash(self) -> str:
        return config_hash(self.model_dump(mode="json"))


class PreRegistration(BaseModel):
    hypothesis_id: str
    primary_metric: str
    primary_horizon: str
    family_id: str
    selection_policy: SelectionPolicy
    stopping_policy: StoppingPolicy
    validation_protocol: str
    note: str = (
        "Internal research-control freeze. Not a claim of external scientific preregistration."
    )

    def identity_hash(self) -> str:
        return config_hash(self.model_dump(mode="json"))


def assert_spec_frozen(original: ResearchSpec, current: ResearchSpec) -> None:
    if original.identity_hash() != current.identity_hash():
        raise OrchestrationError("experiment spec mutated after freeze; bump experiment_version")
