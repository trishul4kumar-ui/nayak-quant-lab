from __future__ import annotations

import pytest

from quantlab.domain.models import ExperimentRun, ExperimentStatus
from quantlab.knowledge.graph import KnowledgeGraph
from quantlab.knowledge.ingest import ingest_ledger_run

pytestmark = pytest.mark.knowledge


def test_legacy_ledger_rows_load_without_knowledge_fields() -> None:
    raw = {
        "id": "legacy-row",
        "name": "old",
        "hypothesis": "h",
        "dataset_version": "v1",
        "universe": ["NSE:TCS"],
    }
    run = ExperimentRun.model_validate(raw)
    assert run.knowledge_snapshot_id == ""
    assert run.knowledge_graph_id == ""
    assert run.claim_id == ""


def test_ledger_run_ingests_as_experiment() -> None:
    graph = KnowledgeGraph()
    run = ExperimentRun(
        id="run-1",
        name="momentum",
        hypothesis="h",
        status=ExperimentStatus.PASSED,
        dataset_version="v1",
        universe=["NSE:TCS"],
        hypothesis_id="H-MOM-001",
        data_kind="synthetic",
        tested_count=4,
        selection_stage="orchestration",
    )
    ingest_ledger_run(graph, run)
    assert any(item.ref_id == "run-1" for item in graph.nodes)
    assert graph.evidence
