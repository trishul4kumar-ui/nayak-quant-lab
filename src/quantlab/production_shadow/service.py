"""Compose observed feed/account evidence with existing shadow engines; no routing occurs here."""

from __future__ import annotations

from datetime import UTC, datetime

from quantlab.broker_gateway.models import GatewaySnapshotBundle
from quantlab.broker_gateway.service import last_snapshot as last_broker_snapshot
from quantlab.core.config import LiveSafetyGates
from quantlab.production_shadow.models import (
    EvidenceLabel,
    ProductionShadowIncident,
    ProductionShadowPolicy,
    ProductionShadowReadiness,
    ProductionShadowRun,
    ShadowCheck,
    ShadowCheckResult,
    ShadowProductionState,
)
from quantlab.production_shadow.repository import put, set_state
from quantlab.realtime_data.hashing import sha256
from quantlab.realtime_data.models import QualityStatus, RealTimeSnapshot
from quantlab.realtime_data.service import inspect as inspect_market_snapshot
from quantlab.realtime_decision.models import RealTimeDecision
from quantlab.reconciliation.models import ReconciliationReport, ReconciliationStatus
from quantlab.reconciliation.repository import last as last_reconciliation
from quantlab.shadow.models import ShadowResult
from quantlab.shadow.state import last_result as last_shadow_result


def start() -> ShadowProductionState:
    """Start assessment mode only; this never opens a provider or broker connection."""
    set_state(ShadowProductionState.RUNNING.value)
    return ShadowProductionState.RUNNING


def stop() -> ShadowProductionState:
    set_state(ShadowProductionState.STOPPED.value)
    return ShadowProductionState.STOPPED


def assess(
    *,
    market: RealTimeSnapshot | None = None,
    broker: GatewaySnapshotBundle | None = None,
    reconciliation: ReconciliationReport | None = None,
    decision: RealTimeDecision | None = None,
    shadow: ShadowResult | None = None,
    policy: ProductionShadowPolicy | None = None,
    observed_at: datetime | None = None,
) -> ProductionShadowRun:
    """Assess evidence at a point in time. Missing or synthetic evidence blocks by design."""
    used_policy = policy or ProductionShadowPolicy()
    used_market = market or inspect_market_snapshot("last")
    used_broker = broker or last_broker_snapshot()
    used_reconciliation = reconciliation or last_reconciliation()
    used_shadow = shadow or last_shadow_result()
    now = observed_at or _timestamp(used_market, used_broker)
    checks: list[ShadowCheck] = []
    _market_checks(used_market, used_policy, checks)
    _broker_checks(used_broker, checks)
    _alignment_check(used_market, used_broker, used_policy, checks)
    _reconciliation_check(used_reconciliation, checks)
    _shadow_checks(used_shadow, checks)
    _decision_check(decision, checks)
    _safety_check(checks)
    readiness = _readiness(checks)
    incidents = tuple(_incidents(checks, now))
    state = (
        ShadowProductionState.BLOCKED
        if readiness.critical_failures
        else ShadowProductionState.RUNNING
    )
    material = {
        "market": used_market.snapshot_hash if used_market else "",
        "broker": used_broker.payload_hash if used_broker else "",
        "reconciliation": used_reconciliation.reconciliation_hash if used_reconciliation else "",
        "decision": decision.decision_hash if decision else "",
        "shadow": used_shadow.cycle.cycle_id if used_shadow else "",
        "policy": used_policy.model_dump(mode="json"),
        "checks": [item.model_dump(mode="json") for item in checks],
        "observed_at": now.isoformat(),
    }
    digest = sha256(material)
    run = ProductionShadowRun(
        shadow_run_id=f"production-shadow-{digest[:12]}",
        market_snapshot_hash=used_market.snapshot_hash if used_market else "",
        broker_snapshot_hash=used_broker.payload_hash if used_broker else "",
        strategy_release_hash=decision.release_hash if decision else "",
        decision_hash=decision.decision_hash if decision else "",
        target_portfolio_hash=(
            decision.target.portfolio_hash if decision and decision.target else ""
        ),
        paper_order_plan_hash=used_shadow.cycle.order_plan_hash if used_shadow else "",
        execution_policy_hash=used_shadow.cycle.execution_policy_hash if used_shadow else "",
        twin_state_hash=used_shadow.checkpoint.payload_hash
        if used_shadow and used_shadow.checkpoint
        else "",
        reconciliation_hash=used_reconciliation.reconciliation_hash if used_reconciliation else "",
        policy=used_policy,
        checks=tuple(checks),
        incidents=incidents,
        readiness=readiness,
        observed_at=now,
        state=state,
        evidence_labels={
            "market": EvidenceLabel.OBSERVED if used_market else EvidenceLabel.NOT_TESTED,
            "broker": EvidenceLabel.OBSERVED if used_broker else EvidenceLabel.NOT_TESTED,
            "decision": EvidenceLabel.COUNTERFACTUAL if decision else EvidenceLabel.NOT_TESTED,
            "orders": EvidenceLabel.SIMULATED if used_shadow else EvidenceLabel.NOT_TESTED,
            "tca": EvidenceLabel.MODELLED if used_shadow else EvidenceLabel.NOT_TESTED,
        },
        run_hash=digest,
    )
    return put(run)


def _market_checks(
    market: RealTimeSnapshot | None,
    policy: ProductionShadowPolicy,
    checks: list[ShadowCheck],
) -> None:
    if market is None:
        checks.append(
            _check("market_snapshot", ShadowCheckResult.NOT_TESTED, "market snapshot missing")
        )
        return
    source = str(market.extras.get("source_manifest", ""))
    provenance_ok = source.startswith("production-observe-only:")
    checks.append(
        _check(
            "market_provenance",
            ShadowCheckResult.PASS
            if provenance_ok or not policy.require_production_provenance
            else ShadowCheckResult.FAIL,
            "production source provenance required"
            if not provenance_ok
            else "production provenance recorded",
        )
    )
    quality_ok = market.quality is QualityStatus.VALID
    checks.append(
        _check(
            "market_quality",
            ShadowCheckResult.PASS if quality_ok else ShadowCheckResult.FAIL,
            f"quality={market.quality.value}",
        )
    )
    checks.append(
        _check(
            "market_sequence",
            ShadowCheckResult.PASS
            if market.sequence_kind.value == "valid"
            else ShadowCheckResult.FAIL,
            f"sequence={market.sequence_kind.value}",
        )
    )


def _broker_checks(broker: GatewaySnapshotBundle | None, checks: list[ShadowCheck]) -> None:
    if broker is None:
        checks.append(
            _check("broker_snapshot", ShadowCheckResult.NOT_TESTED, "broker snapshot missing")
        )
        return
    real_adapter = not broker.adapter_id.startswith("mock")
    checks.append(
        _check(
            "broker_provenance",
            ShadowCheckResult.PASS if real_adapter else ShadowCheckResult.FAIL,
            "read-only broker observation required; mock adapter is diagnostic only",
        )
    )


def _alignment_check(
    market: RealTimeSnapshot | None,
    broker: GatewaySnapshotBundle | None,
    policy: ProductionShadowPolicy,
    checks: list[ShadowCheck],
) -> None:
    if market is None or broker is None:
        checks.append(
            _check(
                "market_broker_alignment",
                ShadowCheckResult.NOT_TESTED,
                "both observations required",
            )
        )
        return
    drift = abs((market.as_of - broker.provenance.source_timestamp).total_seconds())
    checks.append(
        _check(
            "market_broker_alignment",
            ShadowCheckResult.PASS
            if drift <= policy.market_broker_alignment_seconds
            else ShadowCheckResult.FAIL,
            f"alignment_seconds={drift:.3f}",
        )
    )


def _reconciliation_check(report: ReconciliationReport | None, checks: list[ShadowCheck]) -> None:
    if report is None:
        checks.append(
            _check("reconciliation", ShadowCheckResult.NOT_TESTED, "reconciliation report missing")
        )
        return
    passed = report.status in {
        ReconciliationStatus.MATCH,
        ReconciliationStatus.MATCH_WITH_TOLERANCE,
    }
    checks.append(
        _check(
            "reconciliation",
            ShadowCheckResult.PASS if passed else ShadowCheckResult.FAIL,
            report.status.value,
        )
    )


def _shadow_checks(shadow: ShadowResult | None, checks: list[ShadowCheck]) -> None:
    if shadow is None:
        checks.append(
            _check("shadow_cycle", ShadowCheckResult.NOT_TESTED, "simulated shadow cycle missing")
        )
        checks.append(
            _check("deterministic_replay", ShadowCheckResult.NOT_TESTED, "replay evidence missing")
        )
        return
    route_safe = not shadow.broker_routing_enabled and not shadow.live_order_submission_enabled
    checks.append(
        _check(
            "shadow_non_routable",
            ShadowCheckResult.PASS if route_safe else ShadowCheckResult.FAIL,
            "shadow must remain non-routable",
        )
    )
    checks.append(
        _check(
            "deterministic_replay",
            ShadowCheckResult.NOT_TESTED,
            "replay evidence must be supplied explicitly",
        )
    )


def _decision_check(decision: RealTimeDecision | None, checks: list[ShadowCheck]) -> None:
    if decision is None:
        checks.append(
            _check("decision_capture", ShadowCheckResult.NOT_TESTED, "decision capture missing")
        )
    elif decision.target is None:
        checks.append(
            _check("decision_capture", ShadowCheckResult.FAIL, "decision abstained or lacks target")
        )
    else:
        checks.append(
            _check("decision_capture", ShadowCheckResult.PASS, "counterfactual target captured")
        )


def _safety_check(checks: list[ShadowCheck]) -> None:
    gates = LiveSafetyGates()
    safe = not gates.live_trading and not gates.broker_write_enabled and gates.shadow_mode
    checks.append(
        _check(
            "safety_wall",
            ShadowCheckResult.PASS if safe else ShadowCheckResult.FAIL,
            "live and broker-write remain disabled",
        )
    )


def _check(check_id: str, result: ShadowCheckResult, reason: str) -> ShadowCheck:
    return ShadowCheck(
        check_id=check_id,
        result=result,
        critical=True,
        reason=reason,
        evidence_hash=sha256({"check": check_id, "result": result.value, "reason": reason}),
    )


def _readiness(checks: list[ShadowCheck]) -> ProductionShadowReadiness:
    failures = tuple(item.check_id for item in checks if item.blocks)
    return ProductionShadowReadiness(
        dimensions={item.check_id: item.result for item in checks},
        critical_failures=failures,
    )


def _incidents(checks: list[ShadowCheck], now: datetime) -> list[ProductionShadowIncident]:
    return [
        ProductionShadowIncident(
            incident_id=f"shadow-incident-{item.evidence_hash[:12]}",
            severity="CRITICAL",
            detected_at=now,
            source="production_shadow",
            description=item.reason,
            evidence=(item.evidence_hash,),
        )
        for item in checks
        if item.blocks
    ]


def _timestamp(market: RealTimeSnapshot | None, broker: GatewaySnapshotBundle | None) -> datetime:
    if market is not None:
        return market.as_of
    if broker is not None:
        return broker.provenance.captured_at
    return datetime.now(tz=UTC)
