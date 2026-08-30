"""Named orchestration experiments. Coordinates existing engines; does not replace them."""

from __future__ import annotations

from pathlib import Path

from quantlab.domain.models import ExperimentRun
from quantlab.orchestration.budget import ResearchBudget
from quantlab.orchestration.leaks import OrchestrationLeakFlags
from quantlab.orchestration.registry import default_registry
from quantlab.orchestration.report import OrchestrationReport
from quantlab.orchestration.runner import execute_spec
from quantlab.orchestration.specification import ResearchSpec


def run_orchestration_experiment(
    spec: ResearchSpec,
    *,
    ledger_path: Path,
    fabric_root: Path | None = None,
    append: bool = False,
    leaks: OrchestrationLeakFlags | None = None,
    budget: ResearchBudget | None = None,
    frozen: ResearchSpec | None = None,
    hide_failures: bool = False,
    execution_order: list[int] | None = None,
    include_falsification: bool = True,
    include_execution: bool = True,
) -> tuple[OrchestrationReport, ExperimentRun]:
    return execute_spec(
        spec,
        frozen=frozen or spec,
        ledger_path=ledger_path,
        fabric_root=fabric_root,
        append=append,
        leaks=leaks,
        budget=budget,
        hide_failures=hide_failures,
        execution_order=execution_order,
        include_falsification=include_falsification,
        include_execution=include_execution,
    )


def run_named_orchestration_experiment(
    experiment_id: str = "EXP-MOM-001",
    *,
    ledger_path: Path,
    n_days: int = 80,
    fabric_root: Path | None = None,
    append: bool = True,
    leaks: OrchestrationLeakFlags | None = None,
    family_id: str | None = None,
) -> tuple[OrchestrationReport, ExperimentRun]:
    spec = default_registry().get_spec(experiment_id)
    updated = spec.model_copy(update={"n_days": n_days})
    if family_id:
        updated = updated.model_copy(update={"family_id": family_id})
    return run_orchestration_experiment(
        updated,
        frozen=spec.model_copy(update={"n_days": n_days, "family_id": updated.family_id}),
        ledger_path=ledger_path,
        fabric_root=fabric_root,
        append=append,
        leaks=leaks,
    )
