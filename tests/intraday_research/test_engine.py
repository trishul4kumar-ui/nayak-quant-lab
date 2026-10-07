from datetime import UTC, datetime, timedelta
from pathlib import Path

from quantlab.intraday_research.engine import evaluate_signal, features
from quantlab.intraday_research.models import (
    ArrivalState,
    DepthLevel,
    DepthSnapshot,
    ResearchClass,
    ScalpStrategyDefinition,
    TickObservation,
)
from quantlab.intraday_research.replay import ReplayPolicy, replay

NOW = datetime(2026, 10, 8, 5, tzinfo=UTC)


def tick(state: ArrivalState = ArrivalState.VALID) -> TickObservation:
    bid = DepthLevel(
        created_at=NOW, schema_version="intraday-research-v1", price=99.9, quantity=200
    )
    ask = DepthLevel(
        created_at=NOW, schema_version="intraday-research-v1", price=100.1, quantity=100
    )
    depth = DepthSnapshot(
        created_at=NOW,
        schema_version="intraday-research-v1",
        bids=(bid,),
        asks=(ask,),
    )
    return TickObservation(
        created_at=NOW,
        schema_version="intraday-research-v1",
        security_id="NSE:EXAMPLE",
        received_at=NOW,
        processed_at=NOW,
        price=100,
        depth=depth,
        arrival_state=state,
    )


def strategy() -> ScalpStrategyDefinition:
    return ScalpStrategyDefinition(
        created_at=NOW,
        schema_version="intraday-research-v1",
        strategy_id="imbalance",
        version="v1",
        required_features=("top_imbalance", "relative_spread_bps"),
        entry_threshold=0.2,
        maximum_spread_bps=30,
        horizon_seconds=30,
        research_class=ResearchClass.AUTOMATION_RESEARCH_ONLY,
        cost_model_version="cost-v1",
        max_orders_per_interval=0,
    )


def test_deterministic_replay_and_signal_have_no_execution_authority() -> None:
    first = evaluate_signal(tick(), strategy(), now=NOW)
    second = evaluate_signal(tick(), strategy(), now=NOW)
    assert first == second and first.direction == "LONG" and not first.execution_authority
    delayed = replay((tick(),), ReplayPolicy(latency_ms=25, inject_gap_after=0))[0]
    assert delayed.arrival_state is ArrivalState.GAP


def test_missing_depth_and_stale_feed_fail_closed() -> None:
    missing = tick().model_copy(update={"depth": None})
    missing = TickObservation.model_validate(
        missing.model_dump(mode="json", exclude={"content_hash"})
    )
    assert features(missing).quality is ArrivalState.MISSING_DEPTH
    stale = evaluate_signal(tick(), strategy(), now=NOW + timedelta(seconds=31))
    assert stale.direction == "ABSTAIN" and stale.reason == "STALE_FEED"


def test_hot_path_has_no_agent_or_broker_dependency() -> None:
    source = Path("src/quantlab/intraday_research/engine.py").read_text()
    assert "quantlab.agents" not in source
    assert "from quantlab.broker" not in source
