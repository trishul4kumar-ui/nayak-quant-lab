"""Leak flags for the research control plane. None → NOT_TESTED."""

from __future__ import annotations

from pydantic import BaseModel


class OrchestrationLeakFlags(BaseModel):
    experiment_identity_mutation: bool | None = None
    experiment_config_mutation: bool | None = None
    future_experiment_selection: bool | None = None
    future_candidate_selection: bool | None = None
    future_hypothesis_selection: bool | None = None
    hidden_candidate: bool | None = None
    hidden_failed_experiment: bool | None = None
    hidden_search: bool | None = None
    posthoc_stopping: bool | None = None
    multiple_testing_omission: bool | None = None
    family_definition_mutation: bool | None = None
    research_budget_bypass: bool | None = None
    replication_contamination: bool | None = None
    holdout_reuse: bool | None = None
    future_baseline_selection: bool | None = None
    future_model_selection: bool | None = None
    future_execution_selection: bool | None = None
    future_cost_selection: bool | None = None
    lineage_break: bool | None = None
    dataset_snapshot_mismatch: bool | None = None
    result_overwrite: bool | None = None
    parallel_state_leak: bool | None = None
    adaptive_state_cross_contamination: bool | None = None
