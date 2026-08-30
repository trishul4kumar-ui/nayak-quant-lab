"""Compose existing engines. Do not fork feature/covariance/portfolio/capital."""

from __future__ import annotations

from datetime import datetime

from quantlab.capital.definitions import TargetPortfolio
from quantlab.core.config import LiveSafetyGates
from quantlab.realtime_data.hashing import sha256
from quantlab.realtime_data.models import QualityStatus, RealTimeSnapshot
from quantlab.realtime_data.service import snapshot as freeze_snapshot
from quantlab.realtime_decision.audit import append as record_audit
from quantlab.realtime_decision.audit import reset_for_tests as reset_audit
from quantlab.realtime_decision.audit import rows as audit_rows
from quantlab.realtime_decision.errors import DecisionBlocked, UncertifiedReleaseError
from quantlab.realtime_decision.models import (
    AbstentionReason,
    ActorKind,
    CertificationStatus,
    RealTimeDecision,
    StrategyRelease,
    default_uncertified_release,
)
from quantlab.realtime_decision.repository import get as get_decision
from quantlab.realtime_decision.repository import list_ids
from quantlab.realtime_decision.repository import put as put_decision
from quantlab.realtime_decision.repository import reset_for_tests as reset_repo
from quantlab.realtime_decision.state import DecisionState, current, force, transition
from quantlab.realtime_decision.state import reset_for_tests as reset_state
from quantlab.safety.kill_switch import live_release_blocked

CYCLE: tuple[str, ...] = (
    "OBSERVE",
    "VALIDATE",
    "FREEZE",
    "FEATURE",
    "ALPHA",
    "REGIME",
    "MODEL",
    "ENSEMBLE",
    "PORTFOLIO",
    "CAPITAL",
    "RISK",
    "DECISION",
    "AUDIT",
)


def reset_for_tests() -> None:
    reset_state()
    reset_repo()
    reset_audit()


def _assert_safety() -> LiveSafetyGates:
    gates = LiveSafetyGates()
    assert gates.live_trading is False
    assert gates.broker_write_enabled is False
    assert live_release_blocked() is True
    return gates


def _reset_cycle() -> None:
    force(DecisionState.OBSERVING)


def run_realtime_decision(
    *,
    release: StrategyRelease | None = None,
    frozen: RealTimeSnapshot | None = None,
    actor: ActorKind = ActorKind.SYSTEM,
    as_of: datetime | None = None,
) -> RealTimeDecision:
    _assert_safety()
    _reset_cycle()
    transition(DecisionState.VALIDATING)
    snap = frozen or freeze_snapshot(as_of=as_of)
    bound = release or default_uncertified_release(as_of=snap.as_of)
    if actor is ActorKind.AI_SUGGESTION:
        transition(DecisionState.BLOCKED)
        raise DecisionBlocked("AI_SUGGESTION cannot certify, promote, or decide")
    if LiveSafetyGates().live_trading:
        transition(DecisionState.HALTED)
        return _store(_abstain(snap, bound, AbstentionReason.SAFETY_BLOCK, DecisionState.HALTED))
    if snap.quality in {QualityStatus.STALE, QualityStatus.INVALID, QualityStatus.MISSING}:
        next_state = (
            DecisionState.STALE
            if snap.quality is QualityStatus.STALE
            else DecisionState.ABSTAINED
        )
        transition(next_state)
        reason = (
            AbstentionReason.STALE_DATA
            if snap.quality is QualityStatus.STALE
            else AbstentionReason.INVALID_STATE
        )
        return _store(_abstain(snap, bound, reason, current()))
    if bound.certification_status in {
        CertificationStatus.EXPIRED,
        CertificationStatus.REVOKED,
    }:
        transition(DecisionState.BLOCKED)
        return _store(_abstain(snap, bound, AbstentionReason.EXPIRED_CERT, DecisionState.BLOCKED))
    if bound.certification_status in {
        CertificationStatus.UNCERTIFIED,
        CertificationStatus.UNKNOWN,
    }:
        transition(DecisionState.ABSTAINED)
        return _store(
            _abstain(snap, bound, AbstentionReason.UNCERTIFIED_RELEASE, DecisionState.ABSTAINED)
        )
    if bound.expiry_at is not None and bound.expiry_at <= snap.as_of:
        transition(DecisionState.BLOCKED)
        return _store(_abstain(snap, bound, AbstentionReason.EXPIRED_CERT, DecisionState.BLOCKED))
    if bound.release_hash in {"", "uncertified"}:
        raise UncertifiedReleaseError("unknown strategy release")
    transition(DecisionState.READY)
    transition(DecisionState.COMPUTING)
    target = _equal_weight_target(snap, bound)
    transition(DecisionState.DECIDED)
    decided = _decided(snap, bound, target)
    return _store(decided)


def inspect(decision_id: str = "last") -> RealTimeDecision | None:
    return get_decision(decision_id)


def list_decisions() -> list[str]:
    return list_ids()


def audit_history() -> list[dict[str, object]]:
    return audit_rows()


def _equal_weight_target(snap: RealTimeSnapshot, release: StrategyRelease) -> TargetPortfolio:
    names = sorted({row.security_id for row in snap.observations if row.price and row.price > 0})
    n = max(len(names), 1)
    weight = 1.0 / n if names else 0.0
    weights = {name: weight for name in names}
    gross = sum(abs(value) for value in weights.values())
    payload = {
        "snapshot": snap.snapshot_hash,
        "release": release.release_hash,
        "weights": weights,
        "schema": "3.1.0",
    }
    portfolio_hash = sha256(payload)
    return TargetPortfolio(
        portfolio_id=f"tp-{portfolio_hash[:12]}",
        decision_id=f"dec-{portfolio_hash[:12]}",
        timestamp=snap.as_of,
        weights=weights,
        notional_targets={name: 0.0 for name in names},
        gross_exposure=gross,
        net_exposure=gross,
        cash_target=0.0,
        portfolio_hash=portfolio_hash,
        note="Research-only target. Prompt 30 does not construct orders.",
    )


def _abstain(
    snap: RealTimeSnapshot,
    release: StrategyRelease,
    reason: AbstentionReason,
    state: DecisionState,
) -> RealTimeDecision:
    payload = {
        "snapshot": snap.snapshot_hash,
        "release": release.release_hash,
        "reason": reason.value,
        "state": state.value,
    }
    decision_hash = sha256(payload)
    return RealTimeDecision(
        decision_id=f"dec-{decision_hash[:12]}",
        decision_hash=decision_hash,
        snapshot_id=snap.snapshot_id,
        snapshot_hash=snap.snapshot_hash,
        release_id=release.release_id,
        release_hash=release.release_hash,
        state=state.value,
        as_of=snap.as_of,
        target=None,
        abstention=reason,
        cycle=CYCLE,
        extras={"comfortable_with_no_decision": True},
        live_trading=False,
    )


def _decided(
    snap: RealTimeSnapshot,
    release: StrategyRelease,
    target: TargetPortfolio,
) -> RealTimeDecision:
    payload = {
        "snapshot": snap.snapshot_hash,
        "release": release.release_hash,
        "portfolio": target.portfolio_hash,
        "state": DecisionState.DECIDED.value,
    }
    decision_hash = sha256(payload)
    return RealTimeDecision(
        decision_id=f"dec-{decision_hash[:12]}",
        decision_hash=decision_hash,
        snapshot_id=snap.snapshot_id,
        snapshot_hash=snap.snapshot_hash,
        release_id=release.release_id,
        release_hash=release.release_hash,
        state=DecisionState.DECIDED.value,
        as_of=snap.as_of,
        target=target,
        abstention=AbstentionReason.NONE,
        cycle=CYCLE,
        extras={"adaptive": "PREDICT-FREEZE-REALIZE-WHEN-AVAILABLE"},
        live_trading=False,
    )


def _store(item: RealTimeDecision) -> RealTimeDecision:
    put_decision(item)
    record_audit(
        "decision",
        decision_id=item.decision_id,
        state=item.state,
        hash=item.decision_hash,
    )
    assert LiveSafetyGates().live_trading is False
    return item
