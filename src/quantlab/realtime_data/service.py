"""Observe-only real-time market-data gateway. Not a second fabric. Not a broker."""

from __future__ import annotations

from datetime import datetime

from quantlab.core.config import LiveSafetyGates
from quantlab.realtime_data.audit import append as record_audit
from quantlab.realtime_data.audit import reset_for_tests as reset_audit
from quantlab.realtime_data.audit import rows as audit_rows
from quantlab.realtime_data.errors import RealTimeDataError
from quantlab.realtime_data.freeze import freeze, to_market_states
from quantlab.realtime_data.mock import SEED_AS_OF, MockMarketDataAdapter, seed_observations
from quantlab.realtime_data.models import (
    FeedHealth,
    FreshnessStatus,
    MarketObservation,
    MockFeedScenario,
    QualityStatus,
    RealTimeSnapshot,
    SequenceKind,
    SessionState,
)
from quantlab.realtime_data.production import ProductionFeedSource, ProductionMarketDataAdapter
from quantlab.realtime_data.protocol import MarketDataAdapter
from quantlab.realtime_data.replay import ReplayMarketDataAdapter
from quantlab.realtime_data.repository import get as get_snapshot
from quantlab.realtime_data.repository import list_ids
from quantlab.realtime_data.repository import put as put_snapshot
from quantlab.realtime_data.repository import reset_for_tests as reset_repo
from quantlab.realtime_data.state import FeedState, current, is_healthy, transition
from quantlab.realtime_data.state import reset_for_tests as reset_state
from quantlab.safety.kill_switch import live_release_blocked

_ADAPTER: MarketDataAdapter | None = None
_LAST_OBS: tuple[MarketObservation, ...] = ()


def reset_for_tests() -> None:
    global _ADAPTER, _LAST_OBS
    reset_state()
    reset_repo()
    reset_audit()
    _ADAPTER = None
    _LAST_OBS = ()


def set_adapter(adapter: MarketDataAdapter) -> None:
    global _ADAPTER
    _ADAPTER = adapter


def select_adapter(name: str) -> None:
    """Select an explicit adapter. This action never establishes a vendor connection."""
    if name == "mock":
        set_adapter(MockMarketDataAdapter())
        return
    if name == "production":
        source = ProductionFeedSource(source_id="production-unconfigured", priority=1)
        set_adapter(ProductionMarketDataAdapter((source,)))
        return
    raise RealTimeDataError(f"unknown market-data adapter: {name}")


def _adapter() -> MarketDataAdapter:
    global _ADAPTER
    if _ADAPTER is None:
        _ADAPTER = MockMarketDataAdapter()
    return _ADAPTER


def _assert_safety() -> LiveSafetyGates:
    gates = LiveSafetyGates()
    assert gates.live_trading is False
    assert gates.broker_write_enabled is False
    assert live_release_blocked() is True
    return gates


def start(
    scenario: MockFeedScenario | str = MockFeedScenario.NORMAL,
    *,
    adapter_name: str | None = None,
    adapter: MarketDataAdapter | None = None,
) -> FeedHealth:
    _assert_safety()
    value = MockFeedScenario(scenario) if isinstance(scenario, str) else scenario
    if adapter is not None:
        set_adapter(adapter)
    elif adapter_name is None:
        set_adapter(MockMarketDataAdapter(value))
    else:
        select_adapter(adapter_name)
    adapter = _adapter()
    if current() is not FeedState.DISCONNECTED:
        transition(FeedState.DISCONNECTED)
    transition(FeedState.CONNECTING)
    adapter.connect()
    if adapter_name == "production":
        transition(FeedState.CONNECTED)
    elif value is MockFeedScenario.DISCONNECT:
        transition(FeedState.DISCONNECTED)
    else:
        transition(FeedState.CONNECTED)
        if value is MockFeedScenario.STALE:
            transition(FeedState.STALE)
        elif value in {
            MockFeedScenario.MALFORMED,
            MockFeedScenario.GAP,
            MockFeedScenario.DUPLICATE,
            MockFeedScenario.OUT_OF_ORDER,
            MockFeedScenario.CLOCK_DRIFT,
        }:
            transition(FeedState.DEGRADED)
    record_audit("start", state=current().value, source=adapter.source_id)
    return health()


def stop() -> FeedHealth:
    _assert_safety()
    adapter = _adapter()
    adapter.disconnect()
    state = current()
    if state in {
        FeedState.CONNECTED,
        FeedState.DEGRADED,
        FeedState.STALE,
        FeedState.HALTED,
        FeedState.RECOVERING,
        FeedState.UNKNOWN,
        FeedState.CONNECTING,
    }:
        transition(FeedState.DISCONNECTED)
    record_audit("stop", state=current().value)
    return health()


def snapshot(*, as_of: datetime | None = None) -> RealTimeSnapshot:
    _assert_safety()
    adapter = _adapter()
    if current() is FeedState.DISCONNECTED:
        start()
    observed = adapter.poll()
    global _LAST_OBS
    if observed:
        _LAST_OBS = observed
    if isinstance(adapter, ProductionMarketDataAdapter) and not observed and not _LAST_OBS:
        raise RealTimeDataError("production feed has no observations; refusing synthetic fallback")
    rows = observed or _LAST_OBS or seed_observations()
    when = as_of
    if when is None:
        when = max((row.event_time for row in rows), default=SEED_AS_OF)
    provenance: dict[str, object] = {"active_source": adapter.source_id}
    source_manifest = "mock-observe-only:v1"
    if isinstance(adapter, ProductionMarketDataAdapter):
        provenance.update(adapter.source_health())
        source_manifest = "production-observe-only:" + "|".join(adapter.source_priority)
    frozen = freeze(
        rows,
        as_of=when,
        provenance=provenance,
        source_manifest=source_manifest,
    )
    put_snapshot(frozen)
    record_audit("snapshot", snapshot_id=frozen.snapshot_id, hash=frozen.snapshot_hash)
    assert LiveSafetyGates().live_trading is False
    return frozen


def replay() -> RealTimeSnapshot:
    _assert_safety()
    original = get_snapshot("last") or snapshot()
    adapter = ReplayMarketDataAdapter(original.observations)
    adapter.connect()
    rows = adapter.poll()
    provenance = {
        key: value
        for key, value in original.extras.items()
        if key not in {"future_ignored", "source_manifest"}
    }
    replayed = freeze(
        rows,
        as_of=original.as_of,
        provenance=provenance,
        source_manifest=str(original.extras.get("source_manifest", "mock-observe-only:v1")),
    )
    if replayed.snapshot_hash != original.snapshot_hash:
        raise RealTimeDataError("realtime replay mismatch")
    put_snapshot(replayed)
    record_audit("replay", snapshot_id=replayed.snapshot_id, hash=replayed.snapshot_hash)
    return replayed


def inspect(snapshot_id: str = "last") -> RealTimeSnapshot | None:
    return get_snapshot(snapshot_id)


def list_snapshots() -> list[str]:
    return list_ids()


def health() -> FeedHealth:
    _assert_safety()
    last = get_snapshot("last")
    connected = current() in {FeedState.CONNECTED, FeedState.DEGRADED, FeedState.STALE}
    quality = last.quality if last else QualityStatus.UNKNOWN
    overall = _overall(current(), quality, last.freshness if last else FreshnessStatus.UNKNOWN)
    adapter = _adapter()
    active_source = adapter.source_id
    source_priority: tuple[str, ...] = (adapter.source_id,)
    source_switches: tuple[str, ...] = ()
    if isinstance(adapter, ProductionMarketDataAdapter):
        active_source = adapter.source_id
        source_priority = adapter.source_priority
        source_switches = adapter.source_switches
    latency = _latency(last)
    coverage_raw = last.extras.get("coverage") if last is not None else None
    coverage = (
        float(coverage_raw)
        if isinstance(coverage_raw, int | float)
        else 1.0
        if last and last.n_names
        else None
    )
    return FeedHealth(
        feed_connected=connected,
        last_observation_time=last.as_of if last else None,
        observation_age_ms=0.0 if last else None,
        sequence_health=last.sequence_kind if last else SequenceKind.UNKNOWN,
        clock_health="ok" if current() is not FeedState.UNKNOWN else "unknown",
        data_quality=quality,
        session_state=last.session if last else SessionState.UNKNOWN,
        security_mapping_health="ok",
        snapshot_health=quality,
        overall=overall,
        active_source=active_source,
        source_priority=source_priority,
        source_switches=source_switches,
        coverage=coverage,
        event_to_receive_ms=latency[0],
        receive_to_process_ms=latency[1],
        process_to_snapshot_ms=latency[2],
        corporate_action_state="unknown",
        live_trading=False,
        write_enabled=False,
    )


def evaluate_realtime_snapshot(*, as_of: datetime | None = None) -> RealTimeSnapshot:
    return snapshot(as_of=as_of)


def market_states(snapshot_id: str = "last") -> tuple[object, ...]:
    frozen = get_snapshot(snapshot_id)
    if frozen is None:
        return ()
    return to_market_states(frozen)


def audit_history() -> list[dict[str, object]]:
    return audit_rows()


def source_status() -> dict[str, object]:
    """Safe provider metadata only; credentials and endpoints are never exposed."""
    adapter = _adapter()
    if isinstance(adapter, ProductionMarketDataAdapter):
        return adapter.source_health()
    return {
        "active_source": adapter.source_id,
        "source_priority": (adapter.source_id,),
        "source_switches": (),
        "quality_faults": (),
        "connected": current() is not FeedState.DISCONNECTED,
    }


def _overall(state: FeedState, quality: QualityStatus, freshness: FreshnessStatus) -> str:
    if state is FeedState.DISCONNECTED:
        return "disconnected"
    if state is FeedState.HALTED:
        return "halted"
    if state is FeedState.RECOVERING:
        return "recovering"
    if state is FeedState.UNKNOWN or quality is QualityStatus.UNKNOWN:
        return "unknown"
    if (
        state is FeedState.STALE
        or quality is QualityStatus.STALE
        or freshness is FreshnessStatus.STALE
    ):
        return "stale"
    if state is FeedState.DEGRADED or quality is not QualityStatus.VALID:
        return "degraded"
    if is_healthy(state) and quality is QualityStatus.VALID:
        return "healthy"
    return "unknown"


def _latency(
    snapshot: RealTimeSnapshot | None,
) -> tuple[float | None, float | None, float | None]:
    """Report only time deltas whose timestamps were actually observed."""
    if snapshot is None or not snapshot.observations:
        return None, None, None
    row = snapshot.observations[-1]
    event_to_receive = (row.receive_time - row.event_time).total_seconds() * 1_000.0
    receive_to_process = (row.processing_time - row.receive_time).total_seconds() * 1_000.0
    process_to_snapshot = (snapshot.as_of - row.processing_time).total_seconds() * 1_000.0
    return event_to_receive, receive_to_process, process_to_snapshot
