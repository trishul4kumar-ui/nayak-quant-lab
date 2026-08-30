"""Scientific knowledge report. Missing evidence stays NOT_TESTED."""

from __future__ import annotations

from typing import Any

from quantlab.knowledge.graph import KnowledgeGraph
from quantlab.knowledge.query import (
    find_evidence,
    find_failures,
    find_hypothesis,
    find_research_claims,
)


def knowledge_report(graph: KnowledgeGraph, hypothesis_id: str) -> dict[str, Any]:
    hypo = find_hypothesis(graph, hypothesis_id)
    evidence = find_evidence(graph, hypothesis_id)
    claims = find_research_claims(graph, hypothesis_id)
    failures = [
        item.node_id
        for item in find_failures(graph)
        if hypothesis_id in item.metadata.values() or hypothesis_id in item.node_id
    ]
    accounting = graph.accounting[0] if graph.accounting else None
    snap = graph.snapshots[-1] if graph.snapshots else None
    data_kind = evidence[0].data_kind if evidence else "unknown"
    return {
        "WHAT": hypo.statement if hypo else "NOT_TESTED: hypothesis not in memory",
        "WHY": hypo.economic_rationale if hypo else "",
        "DATA": evidence[0].dataset_id if evidence else "NOT_TESTED",
        "METHOD": evidence[0].experiment_id if evidence else "NOT_TESTED",
        "SEARCH": accounting.tested_count if accounting else "NOT_TESTED",
        "SELECTION": accounting.selection_policy if accounting else "NOT_TESTED",
        "RESULT": claims[0].statement if claims else "NOT_TESTED",
        "ROBUSTNESS": evidence[0].integrity_status.value if evidence else "not_tested",
        "EXECUTION": next(
            (
                item.execution_assumption or "NOT_TESTED"
                for item in evidence
                if item.execution_assumption
            ),
            "NOT_TESTED",
        ),
        "FALSIFICATION": failures or ["none recorded"],
        "REPLICATION": [item.replication_id for item in graph.replications] or "NOT_TESTED",
        "LIMITATIONS": claims[0].limitations if claims else ["NOT_TESTED"],
        "STATUS": claims[0].status.value
        if claims
        else (hypo.status.value if hypo else "not_tested"),
        "LINEAGE": hypo.parent_hypothesis_id
        if hypo and hypo.parent_hypothesis_id
        else "seed/human",
        "snapshot": snap.knowledge_snapshot_id if snap else "NOT_TESTED",
        "graph_hash": snap.graph_hash if snap else graph.graph_hash(),
        "data_kind": data_kind,
        "live_trading": False,
        "note": "Knowledge is memory, not authority. Synthetic cannot validate market claims.",
    }
