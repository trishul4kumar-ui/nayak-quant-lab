"""Production paper/shadow composition. Wraps Prompt 18. Never routes live."""

from __future__ import annotations

from datetime import UTC, datetime

from quantlab.capital.definitions import InvestmentDecision, TargetPortfolio
from quantlab.certification.enums import CertificationState
from quantlab.core.errors import ShadowCertificationError, ShadowError, StaleDataError
from quantlab.domain.research import IntegrityReport
from quantlab.paper_oms.library import seed_account, seed_decision, seed_snapshot, seed_target
from quantlab.paper_oms.models import PaperAccount, PaperMarketSnapshot, PaperOMSRequest
from quantlab.research.integrity import evaluate_integrity
from quantlab.shadow.accounting import equity_identity
from quantlab.shadow.audit import record_incident
from quantlab.shadow.checkpoint import build_checkpoint, write_checkpoint
from quantlab.shadow.config import make_config
from quantlab.shadow.cycle import assert_cycle_transition, assert_mode_transition
from quantlab.shadow.enums import (
    CycleStatus,
    IncidentKind,
    IncidentSeverity,
    KillReason,
    ReplayOutcome,
    ResultKind,
    SessionState,
    ShadowMode,
    StalePolicy,
)
from quantlab.shadow.execution import run_paper_execution
from quantlab.shadow.fills import from_paper_fill
from quantlab.shadow.health import scorecard as make_scorecard
from quantlab.shadow.identity import hash_cycle, idempotency_key
from quantlab.shadow.integrity import ShadowLeakFlags
from quantlab.shadow.latency import measure_latency
from quantlab.shadow.library import SEED_SHADOW_ACCOUNT, seed_shadow_account
from quantlab.shadow.market import evaluate_freshness
from quantlab.shadow.models import (
    LatencyRecord,
    ReadinessScorecard,
    ShadowCompare,
    ShadowCycle,
    ShadowOrder,
    ShadowReconciliation,
    ShadowRequest,
    ShadowResult,
)
from quantlab.shadow.order_intent import from_paper_intent
from quantlab.shadow.portfolio import from_paper_account
from quantlab.shadow.reconciliation import reconcile_shadow
from quantlab.shadow.safety import assert_no_ai_override, assert_shadow_only
from quantlab.shadow.session import is_tradable, session_state
from quantlab.shadow.shadow_order import from_paper_order
from quantlab.shadow.snapshot import freeze_snapshot
from quantlab.shadow.state import (
    get_result,
    heartbeat,
    kill_reason,
    last_result,
    lookup,
    mode,
    put_result,
    set_kill,
    set_mode,
)
from quantlab.shadow.synchronization import compare_books

_PAPER_OK = frozenset(
    {
        CertificationState.PAPER_ELIGIBLE,
        CertificationState.PAPER_ACTIVE,
        CertificationState.SHADOW_ELIGIBLE,
        CertificationState.SHADOW_ACTIVE,
        CertificationState.PRELIVE_REVIEW,
        CertificationState.CERTIFIED,
    }
)
_SHADOW_OK = frozenset(
    {
        CertificationState.SHADOW_ELIGIBLE,
        CertificationState.SHADOW_ACTIVE,
        CertificationState.PRELIVE_REVIEW,
        CertificationState.CERTIFIED,
    }
)


def _integrity(
    flags: ShadowLeakFlags,
    *,
    live_trading: bool,
    data_kind: str,
) -> IntegrityReport:
    return evaluate_integrity(
        bars=[],
        states=[],
        as_of_times=[],
        next_bar_fill=True,
        cost_bps=10.0,
        slippage_model="configured",
        live_trading=live_trading,
        n_experiments_in_family=1,
        used_ml=False,
        data_kind=data_kind,
        future_shadow_data=flags.future_shadow_data,
        future_decision_input=flags.future_decision_input,
        future_execution_input=flags.future_execution_input,
        stale_data_decision=flags.stale_data_decision,
        unknown_calendar_execution=flags.unknown_calendar_execution,
        duplicate_cycle=flags.duplicate_cycle,
        duplicate_shadow_order=flags.duplicate_shadow_order,
        shadow_live_confusion=flags.shadow_live_confusion,
        live_route_attempt=flags.live_route_attempt,
        paper_shadow_state_confusion=flags.paper_shadow_state_confusion,
        target_mutation=flags.target_mutation,
        decision_mutation=flags.decision_mutation,
        snapshot_mutation=flags.snapshot_mutation,
        model_version_mutation=flags.model_version_mutation,
        configuration_mutation=flags.configuration_mutation,
        pre_arrival_shadow_fill=flags.pre_arrival_shadow_fill,
        future_shadow_fill=flags.future_shadow_fill,
        partial_fill_hidden=flags.partial_fill_hidden,
        shadow_accounting_break=flags.shadow_accounting_break,
        shadow_reconciliation_break=flags.shadow_reconciliation_break,
        checkpoint_hash_mismatch=flags.checkpoint_hash_mismatch,
        recovery_without_reconciliation=flags.recovery_without_reconciliation,
        certification_expired=flags.certification_expired,
        certification_bypass=flags.certification_bypass,
        kill_switch_bypass=flags.kill_switch_bypass,
        risk_bypass=flags.risk_bypass,
        ai_safety_override=flags.ai_safety_override,
        synthetic_production_confusion=flags.synthetic_production_confusion,
        observed_tca_confusion=flags.observed_tca_confusion,
        broker_confirmation_confusion=flags.broker_confirmation_confusion,
    )


def _certification(requested: ShadowMode, *, require_certified: bool) -> tuple[bool, str]:
    from quantlab.certification.state import last_result as last_cert

    found = last_cert()
    status = found.state.value if found is not None else "absent"
    allowed = _SHADOW_OK if requested is ShadowMode.SHADOW else _PAPER_OK
    eligible = found is not None and found.state in allowed
    if requested is ShadowMode.RESEARCH_PAPER:
        return False, status
    if eligible:
        return True, status
    if require_certified:
        raise ShadowCertificationError(
            f"production {requested.value} refused: certification is {status}"
        )
    return False, status


def _advance(current: CycleStatus, target: CycleStatus) -> CycleStatus:
    assert_cycle_transition(current, target)
    return target


def _account_for(mode_value: ShadowMode, account: PaperAccount | None) -> PaperAccount:
    if account is not None:
        return account
    if mode_value is ShadowMode.PAPER:
        return seed_account()
    return seed_shadow_account()


def halt(*, reason: KillReason) -> None:
    set_kill(reason)
    set_mode(ShadowMode.HALTED)


def start(mode_value: ShadowMode) -> ShadowMode:
    current = mode()
    assert_mode_transition(current, mode_value)
    return set_mode(mode_value)


def stop() -> ShadowMode:
    current = mode()
    if current is ShadowMode.OFF:
        return current
    assert_mode_transition(current, ShadowMode.OFF)
    set_kill(None)
    return set_mode(ShadowMode.OFF)


def pause() -> ShadowMode:
    current = mode()
    assert_mode_transition(current, ShadowMode.PAUSED)
    return set_mode(ShadowMode.PAUSED)


def resume(mode_value: ShadowMode = ShadowMode.RESEARCH_PAPER) -> ShadowMode:
    current = mode()
    assert_mode_transition(current, mode_value)
    set_kill(None)
    return set_mode(mode_value)


def run_shadow_cycle(
    request: ShadowRequest | None = None,
    *,
    decision: InvestmentDecision | None = None,
    target: TargetPortfolio | None = None,
    account: PaperAccount | None = None,
    snapshot: PaperMarketSnapshot | None = None,
    leaks: ShadowLeakFlags | None = None,
) -> ShadowResult:
    used = request or ShadowRequest()
    ignored = used.future_payload_ignored
    del ignored
    gates = assert_shadow_only(live_trading=used.live_trading, route_live=used.route_live)
    assert_no_ai_override(ai_override=used.ai_override)
    flags = leaks or ShadowLeakFlags()
    flags = flags.model_copy(
        update={
            "live_route_attempt": False,
            "shadow_live_confusion": False,
            "ai_safety_override": False,
            "broker_confirmation_confusion": False,
            "observed_tca_confusion": False,
            "kill_switch_bypass": False,
            "certification_bypass": False,
            "risk_bypass": False,
            "paper_shadow_state_confusion": False,
            "target_mutation": False,
            "decision_mutation": False,
            "model_version_mutation": False,
            "configuration_mutation": False,
        }
    )
    if used.data_kind == "synthetic":
        flags = flags.model_copy(update={"synthetic_production_confusion": False})
    elif used.data_kind.upper() == "REAL_MARKET":
        flags = flags.model_copy(update={"synthetic_production_confusion": True})
        raise ShadowError("synthetic_production_confusion: seed data is not REAL_MARKET")
    if used.skip_reconciliation:
        flags = flags.model_copy(update={"recovery_without_reconciliation": True})
        raise ShadowError("recovery_without_reconciliation is FAIL")

    requested = used.mode
    current = mode()
    if kill_reason() is not None or current is ShadowMode.HALTED:
        flags = flags.model_copy(update={"kill_switch_bypass": True})
        raise ShadowError("HALT rejects new exposure; HALT is not AUTO-LIQUIDATE")
    if current is ShadowMode.PAUSED:
        raise ShadowError("engine is PAUSED; no new decisions or orders")
    if current is ShadowMode.OFF:
        assert_mode_transition(current, ShadowMode.RESEARCH_PAPER)
        set_mode(ShadowMode.RESEARCH_PAPER)

    production, cert_status = _certification(
        requested, require_certified=used.require_certified
    )
    effective = requested
    if requested in {ShadowMode.PAPER, ShadowMode.SHADOW} and not production:
        flags = flags.model_copy(update={"certification_expired": True})
        record_incident(
            IncidentKind.CERTIFICATION_EXPIRED,
            f"requested {requested.value} without eligible certification ({cert_status})",
            severity=IncidentSeverity.HIGH,
        )
        effective = ShadowMode.RESEARCH_PAPER
    else:
        flags = flags.model_copy(update={"certification_expired": False})

    used_snapshot = snapshot or seed_snapshot()
    used_decision = decision or seed_decision()
    used_target = target or seed_target()
    used_account = _account_for(effective, account)
    as_of = used_snapshot.as_of
    decision_time = used.decision_time or as_of
    available_time = used.available_time or as_of
    data_timestamp = used.data_timestamp or as_of
    received = used.received_timestamp or as_of
    config = make_config(
        mode=effective,
        strategy_version=used.strategy_version,
        execution_policy=used.execution_policy_id,
        max_data_age_ms=used.max_data_age_ms or 300_000,
        data_source="synthetic_seed" if used.data_kind == "synthetic" else used.data_kind,
    )
    session, _calendar = session_state(decision_time, override=used.session_override)
    del _calendar
    if session is SessionState.UNKNOWN:
        flags = flags.model_copy(update={"unknown_calendar_execution": True})
        record_incident(
            IncidentKind.CALENDAR_UNKNOWN,
            "unknown calendar must never be treated as OPEN",
            severity=IncidentSeverity.CRITICAL,
        )
        halt(reason=KillReason.CALENDAR_UNKNOWN)
        raise ShadowError("unknown calendar is not OPEN")
    flags = flags.model_copy(update={"unknown_calendar_execution": False})

    try:
        freshness = evaluate_freshness(
            data_timestamp=data_timestamp,
            received_timestamp=received,
            available_time=available_time,
            decision_time=decision_time,
            processing_time=decision_time,
            config=config,
            policy=StalePolicy.HALT if used.require_certified else StalePolicy.ABSTAIN,
        )
    except StaleDataError:
        flags = flags.model_copy(update={"stale_data_decision": True})
        record_incident(IncidentKind.DATA_STALE, "stale data cannot generate a trade")
        halt(reason=KillReason.DATA_STALE)
        raise
    flags = flags.model_copy(
        update={
            "future_shadow_data": False,
            "future_decision_input": False,
            "stale_data_decision": False,
        }
    )
    if freshness.stale:
        record_incident(IncidentKind.DATA_STALE, "STALE_DATA; cycle abstains")
        raise StaleDataError("stale market data cannot generate a trade decision")

    status = CycleStatus.CREATED
    status = _advance(status, CycleStatus.VALIDATED)
    frozen = freeze_snapshot(
        used_snapshot, account=used_account, config=config, decision_time=decision_time
    )
    status = _advance(status, CycleStatus.SNAPSHOT_FROZEN)
    flags = flags.model_copy(update={"snapshot_mutation": False})

    tradable = is_tradable(session) or effective is ShadowMode.RESEARCH_PAPER
    if not tradable:
        record_incident(
            IncidentKind.CALENDAR_UNKNOWN,
            f"session {session.value} is not OPEN; abstain",
        )
        status = _advance(status, CycleStatus.ABSTAINED)

    key = idempotency_key(
        strategy_version=config.strategy_version,
        decision_time=decision_time.isoformat(),
        data_snapshot_hash=frozen.snapshot_hash,
        portfolio_state_hash=frozen.portfolio_state_hash,
        configuration_hash=config.configuration_hash,
    )
    existing = lookup(key)
    if existing is not None:
        flags = flags.model_copy(update={"duplicate_cycle": False})
        return existing

    paper_result = None
    orders: list[ShadowOrder] = []
    cycle_stub = f"CYC-{frozen.snapshot_hash[:12]}"
    if status is not CycleStatus.ABSTAINED:
        paper_result = run_paper_execution(
            request=PaperOMSRequest(
                decision_id=used_decision.decision_id,
                account_id=used_account.account_id,
                execution_policy_id=used.execution_policy_id,
                snapshot_id=used_snapshot.snapshot_id,
                as_of=as_of,
                data_kind=used.data_kind,
            ),
            decision=used_decision,
            target=used_target,
            account=used_account,
            snapshot=used_snapshot,
        )
        status = _advance(status, CycleStatus.EXECUTED)
        intents = [from_paper_intent(item, cycle_id=cycle_stub) for item in paper_result.intents]
        orders = [from_paper_order(item, cycle_id=cycle_stub) for item in paper_result.orders]
        order_ids = {item.shadow_order_id for item in orders}
        flags = flags.model_copy(
            update={
                "duplicate_shadow_order": len(order_ids) != len(orders),
                "partial_fill_hidden": False,
                "future_execution_input": False,
                "pre_arrival_shadow_fill": False,
                "future_shadow_fill": False,
            }
        )
        fills = [
            from_paper_fill(
                fill,
                cycle_id=cycle_stub,
                shadow_order_id=f"SHD-{fill.order_id}",
            )
            for fill in paper_result.fills
        ]
        portfolio = from_paper_account(paper_result.account, account_id=used_account.account_id)
        recon = reconcile_shadow(paper_result, portfolio, cycle_id=cycle_stub)
        if recon.breaks:
            flags = flags.model_copy(update={"shadow_reconciliation_break": True})
            record_incident(
                IncidentKind.RECONCILIATION_BREAK,
                "shadow reconciliation break",
                cycle_id=cycle_stub,
            )
            halt(reason=KillReason.RECONCILIATION_BREAK)
            status = _advance(status, CycleStatus.HALTED)
        else:
            flags = flags.model_copy(
                update={
                    "shadow_reconciliation_break": False,
                    "shadow_accounting_break": not equity_identity(
                        paper_result.account, portfolio
                    ),
                }
            )
            status = _advance(status, CycleStatus.RECONCILED)
            status = _advance(status, CycleStatus.COMPLETED)
        compare = compare_books(paper_result, portfolio)
        latency = measure_latency(
            data_time=data_timestamp,
            decision_time=decision_time,
            orders=orders,
            fills=fills,
        )
        paper_account = paper_result.account
    else:
        intents = []
        fills = []
        portfolio = from_paper_account(used_account, account_id=used_account.account_id)
        recon = ShadowReconciliation(
            report_id=f"SHREC-{cycle_stub}",
            status="abstained",
            note="No new exposure. Session or data blocked the cycle.",
        )
        compare = ShadowCompare()
        latency = LatencyRecord()
        paper_account = used_account

    now = datetime(2024, 1, 15, tzinfo=UTC)
    kind = ResultKind.RESEARCH_RESULT
    if requested is ShadowMode.PAPER:
        kind = ResultKind.PAPER_RESULT
    elif requested is ShadowMode.SHADOW:
        kind = ResultKind.SHADOW_RESULT
    cycle = ShadowCycle(
        cycle_id=cycle_stub,
        run_id=cycle_stub,
        decision_time=decision_time,
        market_time=as_of,
        data_snapshot_id=used_snapshot.snapshot_id,
        data_snapshot_hash=frozen.snapshot_hash,
        strategy_version=config.strategy_version,
        feature_snapshot_hash=frozen.feature_snapshot_hash,
        model_snapshot_hash=frozen.model_state_hash,
        ensemble_snapshot_hash=frozen.ensemble_state_hash,
        regime_snapshot_hash=frozen.regime_state_hash,
        risk_snapshot_hash=frozen.risk_state_hash,
        capital_decision_hash=used_decision.decision_hash,
        target_portfolio_hash=used_target.portfolio_hash,
        order_plan_hash=paper_result.run.order_plan_hash if paper_result else "",
        execution_policy_hash=config.execution_policy,
        configuration_hash=config.configuration_hash,
        mode=effective,
        requested_mode=requested,
        status=status,
        created_at=now,
        completed_at=now,
        production_run=production,
        live_trading=False,
        note=(
            f"requested={requested.value} effective={effective.value} "
            f"cert={cert_status} LIVE_TRADING=false ZERO LIVE BROKER ROUTING"
        ),
    )
    _ = hash_cycle(cycle)
    result = ShadowResult(
        cycle=cycle,
        config=config,
        freshness=freshness,
        session=session,
        snapshot=frozen,
        intents=intents,
        orders=orders,
        fills=fills,
        portfolio=portfolio,
        paper_account=paper_account,
        paper=paper_result,
        reconciliation=recon,
        compare=compare,
        latency=latency,
        incidents=[],
        scorecard=ReadinessScorecard(),
        heartbeat=heartbeat(),
        integrity=_integrity(flags, live_trading=False, data_kind=used.data_kind),
        result_kind=kind,
        live_trading=False,
        shadow_mode=gates.shadow_mode,
        broker_routing_enabled=False,
        live_order_submission_enabled=False,
        extras={"idempotency_key": key, "certification_status": cert_status},
    )
    checkpoint = build_checkpoint(result, when=now)
    result = result.model_copy(
        update={"checkpoint": checkpoint, "scorecard": make_scorecard(result)}
    )
    stored = put_result(result, key=key)
    write_checkpoint(stored)
    return stored


def replay_cycle(cycle_id: str = "last") -> ShadowResult:
    original = get_result(cycle_id) or last_result()
    if original is None:
        raise ShadowError("no shadow cycle to replay")
    replayed = run_shadow_cycle(
        ShadowRequest(
            mode=original.cycle.mode,
            decision_time=original.cycle.decision_time,
            available_time=original.freshness.available_time,
            data_timestamp=original.freshness.data_timestamp,
            strategy_version=original.cycle.strategy_version,
            execution_policy_id=original.config.execution_policy,
            data_kind="synthetic",
        ),
        snapshot=seed_snapshot(),
        account=seed_account()
        if original.paper_account.account_id != SEED_SHADOW_ACCOUNT
        else seed_shadow_account(),
    )
    match = (
        replayed.cycle.data_snapshot_hash == original.cycle.data_snapshot_hash
        and replayed.cycle.target_portfolio_hash == original.cycle.target_portfolio_hash
        and replayed.reconciliation.reconciliation_hash
        == original.reconciliation.reconciliation_hash
    )
    outcome = ReplayOutcome.MATCH if match else ReplayOutcome.MISMATCH
    return replayed.model_copy(update={"replay": outcome})
