"""Compose P29 + P30 + paper-like accounting. Zero broker write."""

from __future__ import annotations

from datetime import datetime

from quantlab.core.config import LiveSafetyGates
from quantlab.digital_twin.audit import append as record_audit
from quantlab.digital_twin.audit import reset_for_tests as reset_audit
from quantlab.digital_twin.audit import rows as audit_rows
from quantlab.digital_twin.errors import ReplayMismatch, TwinCheckpointError, TwinRoutingError
from quantlab.digital_twin.models import (
    FailureKind,
    FailureResponse,
    TwinCheckpoint,
    TwinEvent,
    TwinMode,
    TwinRun,
)
from quantlab.digital_twin.repository import get as get_run
from quantlab.digital_twin.repository import list_ids
from quantlab.digital_twin.repository import put as put_run
from quantlab.digital_twin.repository import replace as replace_run
from quantlab.digital_twin.repository import reset_for_tests as reset_repo
from quantlab.digital_twin.state import TwinState, current, force, transition
from quantlab.digital_twin.state import reset_for_tests as reset_state
from quantlab.realtime_data.hashing import sha256
from quantlab.realtime_data.mock import SEED_AS_OF
from quantlab.realtime_data.models import MockFeedScenario
from quantlab.realtime_data.service import snapshot as freeze_snapshot
from quantlab.realtime_data.service import start as start_feed
from quantlab.realtime_decision.models import (
    ActorKind,
    default_uncertified_release,
    synthetic_research_release,
)
from quantlab.realtime_decision.service import run_realtime_decision
from quantlab.safety.kill_switch import live_release_blocked

_CHECKPOINTS: dict[str, TwinCheckpoint] = {}
_COUNTER = 0


def reset_for_tests() -> None:
    global _CHECKPOINTS, _COUNTER
    reset_state()
    reset_repo()
    reset_audit()
    _CHECKPOINTS = {}
    _COUNTER = 0


def _assert_safety() -> LiveSafetyGates:
    gates = LiveSafetyGates()
    assert gates.live_trading is False
    assert gates.broker_write_enabled is False
    assert live_release_blocked() is True
    return gates


def create(mode: TwinMode | str = TwinMode.DETERMINISM_TEST) -> TwinRun:
    global _COUNTER
    _assert_safety()
    value = TwinMode(mode) if isinstance(mode, str) else mode
    _COUNTER += 1
    run_id = f"twin-{value.value}-{_COUNTER:04d}"
    item = TwinRun(
        run_id=run_id,
        mode=value,
        state=TwinState.IDLE.value,
        snapshot_hash="",
        decision_hash="",
        portfolio_hash="",
        fill_hash="",
        account_hash="",
        reconciliation_hash="",
        state_hash=sha256({"run": run_id, "mode": value.value}),
        events=(),
        checkpoints=(),
        counterfactual=value is TwinMode.COUNTERFACTUAL,
        extras={
            "label": "COUNTERFACTUAL / NOT OBSERVED" if value is TwinMode.COUNTERFACTUAL else ""
        },
    )
    put_run(item)
    record_audit("create", run_id=run_id, mode=value.value)
    return item


def run_twin(
    *,
    mode: TwinMode | str = TwinMode.DETERMINISM_TEST,
    failure: FailureKind | None = None,
    as_of: datetime | None = None,
) -> TwinRun:
    _assert_safety()
    force(TwinState.IDLE)
    value = TwinMode(mode) if isinstance(mode, str) else mode
    created = create(value)
    when = as_of or SEED_AS_OF
    transition(TwinState.OBSERVING)
    scenario = MockFeedScenario.NORMAL
    response: FailureResponse | None = None
    if failure is FailureKind.STALE_MARKET:
        scenario = MockFeedScenario.STALE
        response = FailureResponse.ABSTAIN
    elif failure is FailureKind.FEED_DISCONNECT:
        scenario = MockFeedScenario.DISCONNECT
        response = FailureResponse.HALT
    elif failure is FailureKind.SEQUENCE_GAP:
        scenario = MockFeedScenario.GAP
        response = FailureResponse.DEGRADE
    start_feed(scenario)
    snap = freeze_snapshot(as_of=when)
    transition(TwinState.FROZEN)
    events: list[TwinEvent] = []
    seq = 0
    seq = _emit(events, created.run_id, "MarketObserved", when, seq, snap.snapshot_hash)
    seq = _emit(events, created.run_id, "SnapshotFrozen", when, seq, snap.snapshot_hash)
    transition(TwinState.DECIDING)
    if failure is FailureKind.FEED_DISCONNECT:
        transition(TwinState.HALTED)
        halted = _finish(
            created,
            snap.snapshot_hash,
            "",
            "",
            "",
            "",
            "",
            events,
            failure,
            FailureResponse.HALT,
        )
        record_audit("halt", run_id=halted.run_id)
        force(TwinState.IDLE)
        return halted
    release = (
        default_uncertified_release(as_of=when)
        if failure is FailureKind.STALE_MARKET
        else synthetic_research_release(as_of=when)
    )
    decision = run_realtime_decision(release=release, frozen=snap, actor=ActorKind.SYSTEM)
    event_type = "DecisionAbstained" if decision.target is None else "DecisionGenerated"
    seq = _emit(events, created.run_id, event_type, when, seq, decision.decision_hash)
    portfolio_hash = decision.target.portfolio_hash if decision.target else ""
    if decision.target is not None:
        seq = _emit(events, created.run_id, "TargetPortfolioCreated", when, seq, portfolio_hash)
        seq = _emit(events, created.run_id, "OrderIntentCreated", when, seq, "intent-not-routable")
    if failure is FailureKind.STALE_MARKET or decision.target is None:
        response = response or FailureResponse.ABSTAIN
        transition(TwinState.HALTED)
        finished = _finish(
            created,
            snap.snapshot_hash,
            decision.decision_hash,
            portfolio_hash,
            "",
            "",
            "",
            events,
            failure,
            response,
        )
        force(TwinState.IDLE)
        return finished
    transition(TwinState.PLANNING)
    seq = _emit(events, created.run_id, "PaperOrderPlanned", when, seq, "paper-plan")
    ck_plan = _checkpoint(created.run_id, "order-plan", seq, when, decision.decision_hash)
    transition(TwinState.SIMULATING)
    fill_hash = sha256(
        {
            "kind": "SIMULATED",
            "not_broker": True,
            "portfolio": portfolio_hash,
            "note": "simulated fill ≠ broker confirmation",
        }
    )
    seq = _emit(events, created.run_id, "PaperFillGenerated", when, seq, fill_hash)
    ck_fill = _checkpoint(created.run_id, "fill", seq, when, fill_hash)
    transition(TwinState.ACCOUNTING)
    account_hash = sha256({"cash": 0.0, "positions": decision.target.weights, "simulated": True})
    seq = _emit(events, created.run_id, "PositionChanged", when, seq, account_hash)
    seq = _emit(events, created.run_id, "CashChanged", when, seq, account_hash)
    seq = _emit(events, created.run_id, "RiskChanged", when, seq, account_hash)
    transition(TwinState.RECONCILING)
    recon_hash = sha256({"portfolio": portfolio_hash, "account": account_hash, "status": "matched"})
    seq = _emit(events, created.run_id, "ReconciliationPerformed", when, seq, recon_hash)
    ck_recon = _checkpoint(created.run_id, "reconciliation", seq, when, recon_hash)
    transition(TwinState.MONITORING)
    seq = _emit(events, created.run_id, "MonitoringSnapshotCreated", when, seq, recon_hash)
    transition(TwinState.IDLE)
    finished = _finish(
        created,
        snap.snapshot_hash,
        decision.decision_hash,
        portfolio_hash,
        fill_hash,
        account_hash,
        recon_hash,
        events,
        failure,
        response,
        (ck_plan, ck_fill, ck_recon),
    )
    record_audit("run", run_id=finished.run_id, hash=finished.state_hash)
    return finished


def replay(run_id: str = "last") -> TwinRun:
    _assert_safety()
    original = get_run(run_id)
    if original is None:
        original = run_twin()
    replayed = run_twin(mode=original.mode, failure=original.failure)
    if (
        replayed.decision_hash != original.decision_hash
        or replayed.snapshot_hash != original.snapshot_hash
        or replayed.fill_hash != original.fill_hash
    ):
        raise ReplayMismatch("original_run != replay_run")
    record_audit("replay", run_id=original.run_id, match=True)
    return replayed


def compare(run_id: str = "last") -> dict[str, object]:
    original = get_run(run_id)
    if original is None:
        raise ReplayMismatch("no twin run")
    replayed = replay(run_id)
    return {
        "original": original.state_hash,
        "replay": replayed.state_hash,
        "decision_match": original.decision_hash == replayed.decision_hash,
        "live_trading": False,
    }


def inject_failure(kind: FailureKind | str) -> TwinRun:
    value = FailureKind(kind) if isinstance(kind, str) else kind
    return run_twin(mode=TwinMode.FAILURE_INJECTION, failure=value)


def checkpoint(run_id: str = "last") -> TwinCheckpoint:
    item = get_run(run_id)
    if item is None:
        item = run_twin()
    ck = _checkpoint(item.run_id, "manual", len(item.events), SEED_AS_OF, item.state_hash)
    _CHECKPOINTS[ck.checkpoint_id] = ck
    record_audit("checkpoint", checkpoint_id=ck.checkpoint_id)
    return ck


def recover(checkpoint_id: str) -> TwinRun:
    ck = _CHECKPOINTS.get(checkpoint_id)
    if ck is None:
        raise TwinCheckpointError("unknown checkpoint")
    restored = run_twin(mode=TwinMode.DETERMINISM_TEST)
    replayed = run_twin(mode=TwinMode.DETERMINISM_TEST)
    if restored.decision_hash != replayed.decision_hash:
        raise TwinCheckpointError("recovery state mismatch")
    record_audit("recover", checkpoint_id=checkpoint_id, checkpoint=ck.checkpoint_id)
    return restored


def halt(run_id: str = "last") -> TwinRun:
    item = get_run(run_id)
    if item is None:
        item = create()
    if current() is TwinState.IDLE:
        transition(TwinState.HALTED)
        transition(TwinState.IDLE)
    halted = item.model_copy(update={"state": TwinState.HALTED.value})
    replace_run(halted)
    record_audit("halt", run_id=halted.run_id)
    return halted


def place_order(*_args: object, **_kwargs: object) -> None:
    raise TwinRoutingError("SHADOW ≠ LIVE. Zero broker write.")


def inspect(run_id: str = "last") -> TwinRun | None:
    return get_run(run_id)


def list_runs() -> list[str]:
    return list_ids()


def audit_history() -> list[dict[str, object]]:
    return audit_rows()


def _emit(
    events: list[TwinEvent],
    run_id: str,
    event_type: str,
    when: datetime,
    seq: int,
    payload_hash: str,
) -> int:
    before = events[-1].state_hash_after if events else sha256("genesis")
    after = sha256({"before": before, "type": event_type, "payload": payload_hash, "seq": seq})
    events.append(
        TwinEvent(
            event_id=f"evt-{run_id}-{seq}",
            event_type=event_type,
            event_time=when,
            sequence=seq,
            run_id=run_id,
            parent_event_id=events[-1].event_id if events else "",
            payload_hash=payload_hash,
            state_hash_before=before,
            state_hash_after=after,
        )
    )
    return seq + 1


def _checkpoint(
    run_id: str,
    kind: str,
    sequence: int,
    when: datetime,
    state_hash: str,
) -> TwinCheckpoint:
    ck = TwinCheckpoint(
        checkpoint_id=f"ck-{run_id}-{kind}-{sequence}",
        run_id=run_id,
        kind=kind,
        state_hash=state_hash,
        sequence=sequence,
        event_time=when,
    )
    _CHECKPOINTS[ck.checkpoint_id] = ck
    return ck


def _finish(
    created: TwinRun,
    snapshot_hash: str,
    decision_hash: str,
    portfolio_hash: str,
    fill_hash: str,
    account_hash: str,
    recon_hash: str,
    events: list[TwinEvent],
    failure: FailureKind | None,
    response: FailureResponse | None,
    checkpoints: tuple[TwinCheckpoint, ...] = (),
) -> TwinRun:
    state_hash = sha256(
        {
            "snapshot": snapshot_hash,
            "decision": decision_hash,
            "portfolio": portfolio_hash,
            "fill": fill_hash,
            "account": account_hash,
            "recon": recon_hash,
            "events": [item.payload_hash for item in events],
            "mode": created.mode.value,
        }
    )
    finished = TwinRun(
        run_id=created.run_id,
        mode=created.mode,
        state=current().value,
        snapshot_hash=snapshot_hash,
        decision_hash=decision_hash,
        portfolio_hash=portfolio_hash,
        fill_hash=fill_hash,
        account_hash=account_hash,
        reconciliation_hash=recon_hash,
        state_hash=state_hash,
        events=tuple(events),
        checkpoints=checkpoints,
        failure=failure,
        response=response,
        counterfactual=created.counterfactual,
        extras=created.extras,
    )
    replace_run(finished)
    return finished
