"""Freeze a research plan before execution."""

from __future__ import annotations

from quantlab.orchestration.budget import ResearchBudget
from quantlab.orchestration.registry import OrchestrationRegistry, default_registry
from quantlab.orchestration.specification import PreRegistration, ResearchPlan, ResearchSpec


def plan_experiment(
    spec: ResearchSpec,
    *,
    budget: ResearchBudget | None = None,
    registry: OrchestrationRegistry | None = None,
) -> ResearchPlan:
    store = registry or default_registry()
    cap = budget or ResearchBudget()
    plan = ResearchPlan(
        plan_id=f"plan:{spec.experiment_id}:{spec.experiment_version}",
        spec=spec,
        budget_max_candidates=cap.max_candidates,
        budget_max_experiments=cap.max_experiments,
    )
    store.put_plan(plan)
    return plan


def preregister(spec: ResearchSpec) -> PreRegistration:
    return PreRegistration(
        hypothesis_id=spec.hypothesis_id,
        primary_metric=spec.primary_metric,
        primary_horizon="1d",
        family_id=spec.family_id,
        selection_policy=spec.selection_policy,
        stopping_policy=spec.stopping_policy,
        validation_protocol=spec.validation_protocol,
    )
