"""App-layer research-orchestration services. CLI and desktop call these."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from quantlab.core.config import get_settings
from quantlab.data.fabric.layout import resolve_fabric_root
from quantlab.models.registry import ExperimentLedger
from quantlab.orchestration.comparison import compare_candidates
from quantlab.orchestration.experiment import run_named_orchestration_experiment
from quantlab.orchestration.family import degrees_of_freedom
from quantlab.orchestration.lineage import build_graph
from quantlab.orchestration.multiple_testing import family_correction
from quantlab.orchestration.pareto import pareto_front
from quantlab.orchestration.planner import plan_experiment
from quantlab.orchestration.registry import (
    default_registry,
    get_family,
    get_hypothesis,
    get_spec,
    list_families,
    list_hypotheses,
    list_specs,
)
from quantlab.orchestration.replication import replication_identity
from quantlab.orchestration.report import OrchestrationReport
from quantlab.orchestration.snapshot import DatasetSnapshot
from quantlab.orchestration.specification import ResearchSpec


def _ledger_path(raw: str) -> Path:
    if raw:
        return Path(raw)
    return Path(get_settings().experiment_ledger_path)


def hypothesis_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in list_hypotheses():
        rows.append(
            {
                "hypothesis_id": item.hypothesis_id,
                "version": item.version,
                "title": item.title,
                "status": item.status.value,
                "identity": item.identity_hash(),
                "null_hypothesis": item.null_hypothesis,
            }
        )
    return rows


def inspect_hypothesis(hypothesis_id: str) -> dict[str, Any]:
    item = get_hypothesis(hypothesis_id)
    payload = item.model_dump(mode="json")
    payload["identity_hash"] = item.identity_hash()
    payload["note"] = (
        "Orchestration hypothesis. Distinct from domain.research.ResearchHypothesis. "
        "Registration is not evidence."
    )
    return payload


def create_hypothesis(hypothesis_id: str, title: str, description: str) -> dict[str, Any]:
    from quantlab.orchestration.hypothesis import HypothesisSpec

    spec = HypothesisSpec(
        hypothesis_id=hypothesis_id,
        title=title,
        description=description,
        provenance="cli_create",
    )
    default_registry().register_hypothesis(spec)
    return inspect_hypothesis(hypothesis_id)


def compare_hypotheses(left_id: str, right_id: str) -> dict[str, Any]:
    left = get_hypothesis(left_id)
    right = get_hypothesis(right_id)
    return {
        "a": left.hypothesis_id,
        "b": right.hypothesis_id,
        "same_identity": left.identity_hash() == right.identity_hash(),
        "identity_a": left.identity_hash(),
        "identity_b": right.identity_hash(),
        "note": "Identity compare is not a Sharpe rank.",
    }


def experiment_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in list_specs():
        rows.append(
            {
                "experiment_id": item.experiment_id,
                "version": item.experiment_version,
                "hypothesis_id": item.hypothesis_id,
                "family_id": item.family_id,
                "type": item.experiment_type.value,
                "identity": item.identity_hash(),
            }
        )
    return rows


def inspect_experiment(experiment_id: str) -> dict[str, Any]:
    spec = get_spec(experiment_id)
    payload = spec.model_dump(mode="json")
    payload["identity_hash"] = spec.identity_hash()
    payload["note"] = "Frozen spec. Running it coordinates existing engines."
    return payload


def plan_named_experiment(experiment_id: str) -> dict[str, Any]:
    spec = get_spec(experiment_id)
    plan = plan_experiment(spec)
    return {
        "plan_id": plan.plan_id,
        "identity_hash": plan.identity_hash(),
        "experiment_id": spec.experiment_id,
        "budget_max_candidates": plan.budget_max_candidates,
        "note": "Plan is frozen. Changing it is a new version.",
    }


def run_named_experiment(
    experiment_id: str,
    *,
    ledger: str = "",
    n_days: int = 80,
    append: bool = True,
) -> tuple[OrchestrationReport, dict[str, Any]]:
    report, run = run_named_orchestration_experiment(
        experiment_id,
        ledger_path=_ledger_path(ledger),
        n_days=n_days,
        fabric_root=resolve_fabric_root(),
        append=append,
    )
    summary = _summary(report, run.id)
    try:
        from quantlab.knowledge.ingest import persist_orchestration_report

        persist_orchestration_report(report, _ledger_path(ledger))
    except Exception as exc:  # noqa: BLE001 — knowledge must not fail a recorded experiment
        summary["knowledge_ingest"] = f"WARN: {exc}"
    return report, summary


def _summary(report: OrchestrationReport, ledger_id: str) -> dict[str, Any]:
    return {
        "experiment_id": report.experiment_id,
        "ledger_id": ledger_id,
        "hypothesis_id": report.hypothesis_id,
        "family_id": report.family_id,
        "identity_hash": report.identity_hash,
        "gate_outcome": report.gate.outcome.value,
        "data_kind": report.data_kind,
        "attempted": report.discovery.attempted,
        "failed": report.discovery.failed,
        "selected_candidate": report.selected_candidate,
        "quality": report.quality.value,
        "status": report.status.value,
        "narrative": report.as_narrative(),
        "live_trading": False,
        "note": report.note,
    }


def family_payload(family_id: str) -> dict[str, Any]:
    family = get_family(family_id)
    space = default_registry().get_search_space(family.search_space_id)
    dof = degrees_of_freedom(family, space, tested_count=0)
    payload = family.model_dump(mode="json")
    payload["identity_hash"] = family.identity_hash()
    payload["search_cells"] = space.size()
    payload["degrees_of_freedom"] = dof.model_dump(mode="json")
    return payload


def lineage_payload(experiment_id: str) -> dict[str, Any]:
    spec = get_spec(experiment_id)
    graph = build_graph(
        hypothesis_id=spec.hypothesis_id,
        family_id=spec.family_id,
        candidate_ids=[],
        parent_experiment=spec.experiment_id,
    )
    return graph.model_dump(mode="json")


def orchestration_report(experiment_id: str, *, ledger: str = "") -> dict[str, Any]:
    found = ExperimentLedger(_ledger_path(ledger)).get(experiment_id)
    if found is None:
        for run in ExperimentLedger(_ledger_path(ledger)).list_runs():
            if run.orchestration_id == experiment_id and not run.parent_experiment_id:
                found = run
                break
    if found is None:
        return {"error": "experiment not found"}
    return found.model_dump(mode="json")


def last_orchestration_experiment_row(runtime: Any) -> dict[str, Any] | None:
    runs = [
        run
        for run in runtime.ledger.list_runs()
        if run.selection_stage == "orchestration" and not run.parent_experiment_id
    ]
    if not runs:
        return None
    run = runs[-1]
    return {
        "id": run.id,
        "orchestration_id": run.orchestration_id,
        "hypothesis_id": run.hypothesis_id,
        "family_id": run.research_family_id,
        "gate_outcome": run.gate_outcome,
        "data_kind": run.data_kind,
        "candidate_count": run.candidate_count,
        "tested_count": run.tested_count,
        "identity": run.config_hash,
    }


def replicate_named(
    experiment_id: str,
    *,
    ledger: str = "",
    n_days: int = 80,
) -> dict[str, Any]:
    spec = get_spec(experiment_id)
    report, summary = run_named_experiment(experiment_id, ledger=ledger, n_days=n_days)
    replica = spec.model_copy()
    snap = DatasetSnapshot(
        dataset_id=report.dataset_id,
        dataset_version="",
        snapshot_id=report.snapshot_id,
        checksum="",
        data_kind=report.data_kind,
        n_days=n_days,
    )
    ident = replication_identity(spec, replica, snap, snap)
    payload = dict(summary)
    payload["replication"] = ident.model_dump(mode="json")
    return payload


def cancel_experiment(experiment_id: str) -> dict[str, Any]:
    spec = get_spec(experiment_id)
    return {
        "experiment_id": spec.experiment_id,
        "cancelled": False,
        "note": (
            "Ledger rows are append-only. Cancel does not rewrite history. "
            "Record a new FAILED child instead of mutating a completed experiment."
        ),
    }


def research_status_payload() -> dict[str, Any]:
    return {
        "hypotheses": len(list_hypotheses()),
        "families": len(list_families()),
        "experiments": len(list_specs()),
        "live_trading": False,
        "note": "Research Control Plane. Prompt 05 remains the only promotion gate.",
    }


def family_multiple_testing(family_id: str, p_values: list[float] | None = None) -> dict[str, Any]:
    family = get_family(family_id)
    report = family_correction(p_values or [], method=family.multiple_testing_method)
    return report.model_dump(mode="json")


def compare_orchestration_candidates(report: OrchestrationReport) -> dict[str, Any]:
    return compare_candidates(report.candidates).model_dump(mode="json")


def pareto_payload(report: OrchestrationReport) -> dict[str, Any]:
    return pareto_front(report.candidates).model_dump(mode="json")


def as_spec_dump(spec: ResearchSpec) -> dict[str, Any]:
    return spec.model_dump(mode="json")
