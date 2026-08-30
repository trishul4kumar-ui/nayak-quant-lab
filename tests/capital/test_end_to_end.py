from __future__ import annotations

from pathlib import Path

import pytest

from quantlab import __version__
from quantlab.capital.allocator import allocate
from quantlab.capital.experiment import run_named_allocation
from quantlab.capital.library import seed_request
from quantlab.core.config import LiveSafetyGates
from quantlab.core.errors import SafetyError
from quantlab.knowledge.entities import NodeType
from quantlab.knowledge.graph import KnowledgeGraph
from quantlab.knowledge.ingest import ingest_capital_decision
from quantlab.models.registry import ExperimentLedger

pytestmark = pytest.mark.capital


def test_live_trading_fails_closed() -> None:
    assert LiveSafetyGates().live_trading is False
    with pytest.raises(SafetyError):
        allocate(seed_request(live_trading=True))


def test_adversarial_future_payload_does_not_change_decision() -> None:
    request = seed_request()
    first = allocate(request)
    future = request.model_copy(
        update={
            "future_payload_ignored": {
                "t_plus_1_return": "0.99",
                "future_volume": "1e12",
                "future_drawdown": "0.4",
            }
        }
    )
    second = allocate(future)
    assert first.decision.decision_hash == second.decision.decision_hash
    assert first.decision.target_weights == second.decision.target_weights


def test_end_to_end_ledger_and_knowledge(tmp_path: Path) -> None:
    assert __version__ == "3.1.0"
    ledger = tmp_path / "ledger.jsonl"
    result, run = run_named_allocation(ledger_path=ledger, append=True)
    assert run.selection_stage == "capital_allocation"
    assert run.decision_id == result.decision.decision_id
    loaded = ExperimentLedger(ledger).get(run.id)
    assert loaded is not None
    assert loaded.target_portfolio_hash == result.target.portfolio_hash
    graph = KnowledgeGraph(graph_id="kg-capital-test")
    ingest_capital_decision(graph, result.decision)
    types = {item.node_type for item in graph.nodes}
    assert NodeType.INVESTMENT_DECISION in types
    assert NodeType.CAPITAL_POLICY in types
    assert NodeType.TARGET_PORTFOLIO in types
    assert any(edge.relationship_type.value == "tested_by" for edge in graph.edges)
    assert "Order" not in result.decision.note or "not an order" in result.decision.note.lower()
    assert result.decision.live_trading is False
    assert result.target.note.startswith("Target")
