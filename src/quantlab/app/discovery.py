"""App-layer discovery services. CLI and desktop call these."""

from __future__ import annotations

import random
from pathlib import Path
from typing import Any

from quantlab.core.config import get_settings
from quantlab.data.fabric.layout import resolve_fabric_root
from quantlab.discovery.complexity import complexity
from quantlab.discovery.crossover import crossover
from quantlab.discovery.experiment import run_named_discovery_search
from quantlab.discovery.generator import human_hypothesis, seed_expressions
from quantlab.discovery.grammar import GrammarSpec
from quantlab.discovery.mutation import mutate
from quantlab.discovery.redundancy import feature_overlap
from quantlab.discovery.registry import get_family, list_families
from quantlab.discovery.symbolic import simplify
from quantlab.models.registry import ExperimentLedger


def _ledger_path(raw: str) -> Path:
    if raw:
        return Path(raw)
    return Path(get_settings().experiment_ledger_path)


def family_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in list_families():
        rows.append(
            {
                "family_id": item.family_id,
                "title": item.title,
                "max_depth": item.grammar.max_depth,
                "population": item.budget.population_size,
                "generations": item.budget.n_generations,
                "note": item.note,
            }
        )
    return rows


def inspect_family(family_id: str) -> dict[str, Any]:
    item = get_family(family_id)
    seeds = [node.canonical_text() for node in seed_expressions(item.grammar)]
    payload = item.model_dump(mode="json")
    payload["seeds"] = seeds
    payload["note"] = (
        "Discovery family. Expressions are hypotheses. "
        "Registration is not evidence. Synthetic cannot promote."
    )
    return payload


def run_named_search(
    family_id: str = "GP-MOM-VOL-001",
    *,
    ledger: str = "",
    n_days: int = 80,
) -> tuple[Any, dict[str, Any]]:
    family = get_family(family_id)
    report, run = run_named_discovery_search(
        family_id,
        ledger_path=_ledger_path(ledger),
        n_days=n_days,
        fabric_root=resolve_fabric_root(),
        budget=family.budget,
        append=True,
    )
    summary = {
        "discovery_run_id": run.discovery_run_id,
        "family_id": run.search_family_id,
        "expression_hash": run.expression_hash,
        "elite": report.elite_text,
        "tested_count": run.tested_count,
        "gate_outcome": run.gate_outcome,
        "data_kind": run.data_kind,
        "selection_stage": run.selection_stage,
        "live_trading": False,
        "identity": run.config_hash,
    }
    try:
        from quantlab.knowledge.ingest import persist_discovery_report

        persist_discovery_report(report, _ledger_path(ledger))
    except Exception as exc:  # noqa: BLE001 — knowledge must not fail a recorded search
        summary["knowledge_ingest"] = f"WARN: {exc}"
    return report, summary


def last_discovery_experiment_row(runtime: Any) -> dict[str, Any] | None:
    runs = [run for run in runtime.ledger.list_runs() if run.selection_stage == "discovery"]
    if not runs:
        return None
    run = runs[-1]
    return {
        "id": run.id,
        "family_id": run.search_family_id or run.research_family_id,
        "expression_hash": run.expression_hash,
        "gate_outcome": run.gate_outcome,
        "data_kind": run.data_kind,
        "tested_count": run.tested_count,
        "novelty": run.novelty_class,
        "identity": run.config_hash,
    }


def last_discovery_payload(ledger: str = "") -> dict[str, Any]:
    runs = [
        run
        for run in ExperimentLedger(_ledger_path(ledger)).list_runs()
        if run.selection_stage == "discovery"
    ]
    if not runs:
        return {"error": "no discovery runs"}
    return runs[-1].model_dump(mode="json")


def lineage_payload(family_id: str, ledger: str = "") -> dict[str, Any]:
    last = last_discovery_payload(ledger)
    if "error" in last:
        return last
    return {
        "family_id": family_id,
        "expression_hash": last.get("expression_hash"),
        "generation": last.get("generation"),
        "note": "Full candidate lineage is in artifacts/discovery.json",
    }


def archive_payload(ledger: str = "") -> dict[str, Any]:
    last = last_discovery_payload(ledger)
    if "error" in last:
        return last
    return {
        "tested_count": last.get("tested_count"),
        "expression_hash": last.get("expression_hash"),
        "note": "Archive is append-only. Losers remain in discovery.json.",
    }


def pareto_payload(ledger: str = "") -> dict[str, Any]:
    last = last_discovery_payload(ledger)
    if "error" in last:
        return last
    return {
        "elite": last.get("expression_hash"),
        "complexity_score": last.get("complexity_score"),
        "novelty": last.get("novelty_class"),
        "note": "Pareto is IC vs complexity on the train fold, not Sharpe.",
    }


def replicate_named_search(
    family_id: str,
    *,
    ledger: str = "",
    n_days: int = 80,
) -> dict[str, Any]:
    report_a, summary_a = run_named_search(family_id, ledger=ledger, n_days=n_days)
    report_b, summary_b = run_named_search(family_id, ledger=ledger, n_days=n_days)
    return {
        "first": summary_a,
        "second": summary_b,
        "same_elite": report_a.elite_hash == report_b.elite_hash,
        "note": "Replay uses the same frozen seed and grammar. A new snapshot is a new lineage.",
    }


def evaluate_expression_text(text: str) -> dict[str, Any]:
    node = human_hypothesis(text, GrammarSpec())
    return {
        "canonical": node.canonical_text(),
        "hash": node.identity_hash(),
        "features": node.feature_names(),
        "note": "Evaluation of IC requires a search run; this is structure only.",
    }


def mutate_seed(*, do_crossover: bool = False) -> dict[str, Any]:
    grammar = GrammarSpec()
    seeds = seed_expressions(grammar)
    rng = random.Random(7)
    if do_crossover:
        a, b, p1, p2 = crossover_pair(seeds[0], seeds[1], rng)
        return {
            "child_a": a.canonical_text(),
            "child_b": b.canonical_text(),
            "parents": [p1, p2],
        }
    node, op = mutate(seeds[0], rng, grammar)
    return {"mutated": simplify(node).canonical_text(), "op": op}


def crossover_pair(left: Any, right: Any, rng: random.Random) -> Any:
    return crossover(left, right, rng)


def simplify_seed() -> dict[str, Any]:
    from quantlab.discovery.expression import binary, constant_node, feature_node

    node = binary("add", feature_node("momentum_20"), constant_node(0.0))
    return {"before": node.canonical_text(), "after": simplify(node).canonical_text()}


def compare_expressions() -> dict[str, Any]:
    seeds = seed_expressions(GrammarSpec())
    left, right = seeds[0], seeds[1]
    return {
        "left": left.canonical_text(),
        "right": right.canonical_text(),
        "same_hash": left.identity_hash() == right.identity_hash(),
        "overlap": feature_overlap(left, right),
    }


def redundancy_payload() -> dict[str, Any]:
    seeds = seed_expressions(GrammarSpec())
    return {
        "pairs": [
            {
                "a": seeds[i].canonical_text(),
                "b": seeds[j].canonical_text(),
                "overlap": feature_overlap(seeds[i], seeds[j]),
            }
            for i in range(len(seeds))
            for j in range(i + 1, len(seeds))
        ][:8]
    }


def complexity_payload() -> dict[str, Any]:
    return {
        "seeds": [
            {"text": node.canonical_text(), "score": complexity(node).score}
            for node in seed_expressions(GrammarSpec())
        ]
    }


def validate_named(family_id: str, *, ledger: str = "", n_days: int = 80) -> dict[str, Any]:
    report, summary = run_named_search(family_id, ledger=ledger, n_days=n_days)
    payload = dict(summary)
    payload["train_ic"] = report.train_ic
    payload["validation_ic"] = report.validation_ic
    payload["holdout_ic"] = report.holdout_ic
    payload["holdout_note"] = "Holdout is recorded, not used for selection."
    return payload
