"""Discovery leak flags. Actual PASS/FAIL lives in quantlab.research.integrity."""

from __future__ import annotations

from pydantic import BaseModel


class DiscoveryLeakFlags(BaseModel):
    future_expression_input: bool | None = None
    future_candidate_generation: bool | None = None
    future_search_state: bool | None = None
    future_fitness: bool | None = None
    future_selection: bool | None = None
    future_mutation: bool | None = None
    future_crossover: bool | None = None
    future_feature: bool | None = None
    posthoc_search_budget: bool | None = None
    search_space_omission: bool | None = None
    candidate_lineage_break: bool | None = None
    expression_mutation: bool | None = None
    future_redundancy: bool | None = None
    future_novelty: bool | None = None
    future_complexity_selection: bool | None = None
    label_used_as_feature: bool | None = None
    hidden_candidate: bool | None = None
    posthoc_stopping: bool | None = None
    holdout_contaminated: bool | None = None
    holdout_reuse: bool | None = None
    test_used_for_selection: bool = False
