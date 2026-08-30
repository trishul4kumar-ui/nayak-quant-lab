from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from quantlab import __version__
from quantlab.core.config import LiveSafetyGates
from quantlab.core.errors import (
    LookAheadError,
    ShadowError,
    StaleDataError,
)
from quantlab.domain.research import CheckResult
from quantlab.knowledge.entities import NodeType
from quantlab.knowledge.graph import KnowledgeGraph
from quantlab.knowledge.ingest import ingest_shadow
from quantlab.paper_oms.library import seed_snapshot
from quantlab.paper_oms.state import reset as reset_paper
from quantlab.shadow.enums import (
    ReplayOutcome,
    SessionState,
    ShadowMode,
)
from quantlab.shadow.models import ShadowRequest
from quantlab.shadow.service import replay_cycle, run_shadow_cycle
from quantlab.shadow.state import last_result
from quantlab.shadow.state import reset as reset_shadow

pytestmark = pytest.mark.shadow


@pytest.fixture(autouse=True)
def _isolate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "quantlab.shadow.checkpoint.default_path",
        lambda: tmp_path / "shadow_checkpoint.json",
    )
    reset_shadow()
    reset_paper()
    yield
    reset_shadow()
    reset_paper()


def test_version() -> None:
    assert __version__ == "3.1.0"


def test_seed_cycle_is_not_live() -> None:
    gates = LiveSafetyGates()
    assert gates.live_trading is False
    assert gates.shadow_mode is True
    assert gates.broker_routing_enabled is False
    assert gates.live_order_submission_enabled is False
    result = run_shadow_cycle()
    assert result.live_trading is False
    assert result.shadow_mode is True
    assert result.broker_routing_enabled is False
    assert result.cycle.production_run is False
    assert result.cycle.mode is ShadowMode.RESEARCH_PAPER
    assert result.orders
    assert result.fills
    assert all(not item.routable for item in result.orders)
    assert all(not item.broker_confirmed for item in result.fills)
    assert result.portfolio.book.value == "shadow_position"
    assert result.integrity.checks["live_route_attempt"] is CheckResult.PASS
    assert "REAL_MARKET" not in result.note


def test_idempotent_duplicate_cycle() -> None:
    first = run_shadow_cycle()
    second = run_shadow_cycle()
    assert first.cycle.cycle_id == second.cycle.cycle_id
    assert first.cycle.data_snapshot_hash == second.cycle.data_snapshot_hash
    assert len(second.orders) == len(first.orders)


def test_replay_matches() -> None:
    original = run_shadow_cycle()
    replayed = replay_cycle(original.cycle.cycle_id)
    assert replayed.replay is ReplayOutcome.MATCH
    assert replayed.cycle.data_snapshot_hash == original.cycle.data_snapshot_hash


@pytest.mark.parametrize(
    ("delta_hours", "error_type"),
    [
        (24, StaleDataError),
        (-1, LookAheadError),
    ],
)
def test_freshness_and_pit(delta_hours: int, error_type: type[Exception]) -> None:
    as_of = datetime(2024, 1, 15, tzinfo=UTC)
    if delta_hours > 0:
        request = ShadowRequest(
            decision_time=as_of + timedelta(hours=delta_hours),
            data_timestamp=as_of,
            available_time=as_of,
            received_timestamp=as_of,
            max_data_age_ms=1,
        )
    else:
        request = ShadowRequest(
            decision_time=as_of,
            available_time=as_of + timedelta(hours=1),
            data_timestamp=as_of,
            received_timestamp=as_of,
        )
    with pytest.raises(error_type):
        run_shadow_cycle(request, snapshot=seed_snapshot())


def test_unknown_calendar_is_not_open() -> None:
    with pytest.raises(ShadowError, match="unknown calendar"):
        run_shadow_cycle(ShadowRequest(session_override=SessionState.UNKNOWN))


def test_partial_fills_and_residuals_visible() -> None:
    snapshot = seed_snapshot(volumes={"NSE:AAA": 1.0, "NSE:BBB": None, "NSE:CCC": 1.0})
    result = run_shadow_cycle(snapshot=snapshot)
    remaining = [item.remaining_quantity for item in result.orders]
    residuals = [item.residual_quantity for item in result.orders]
    assert remaining
    assert residuals is not None
    assert result.integrity.checks["partial_fill_hidden"] is CheckResult.PASS
    assert any(item.remaining_quantity >= 0 for item in result.orders)


def test_cash_and_equity_identity() -> None:
    result = run_shadow_cycle()
    expected = result.portfolio.cash + result.portfolio.market_value
    assert abs(result.portfolio.equity - expected) <= 1e-6
    assert abs(result.paper_account.equity - expected) <= 1e-6
    assert not result.reconciliation.breaks


def test_knowledge_nodes() -> None:
    result = run_shadow_cycle()
    graph = KnowledgeGraph(graph_id="kg-test")
    ingest_shadow(graph, result)
    types = {item.node_type for item in graph.nodes}
    assert NodeType.SHADOW_CYCLE in types
    assert NodeType.SHADOW_ORDER in types
    assert NodeType.SHADOW_FILL in types
    assert NodeType.SHADOW_POSITION in types
    assert NodeType.SHADOW_RECONCILIATION in types
    assert last_result() is result
