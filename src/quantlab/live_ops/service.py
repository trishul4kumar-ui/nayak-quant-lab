"""Evidence-first monitoring, alerting, and human-led incident management."""
# ruff: noqa: E501

from __future__ import annotations

from datetime import UTC, datetime

from quantlab.core.config import LiveSafetyGates
from quantlab.live_ops.models import (
    AlertEvent,
    AlertRule,
    EscalationPolicy,
    HealthSignal,
    Incident,
    IncidentEvent,
    IncidentEvidence,
    IncidentState,
    OperationalSnapshot,
    ResponseAction,
    ResponseActionKind,
    Severity,
)
from quantlab.live_ops.repository import (
    actions,
    alert,
    alerts,
    incident,
    incident_by_id,
    incidents,
    put_action,
    put_alert,
    put_incident,
    put_snapshot,
)
from quantlab.realtime_data.hashing import sha256
from quantlab.safety.kill_switch import activate, is_active
from quantlab.safety.models import KillScope


def _now() -> datetime:
    return datetime.now(tz=UTC)


_RULES = (
    AlertRule(
        rule_id="gateway-unavailable",
        component="restricted_gateway",
        trigger_statuses=("BLOCKED", "UNKNOWN"),
        severity=Severity.HIGH,
    ),
    AlertRule(
        rule_id="safety-kill",
        component="safety",
        trigger_statuses=("KILL_ACTIVE",),
        severity=Severity.CRITICAL,
    ),
    AlertRule(
        rule_id="reconciliation",
        component="reconciliation",
        trigger_statuses=("MISMATCH", "UNKNOWN"),
        severity=Severity.HIGH,
    ),
    AlertRule(
        rule_id="market-data",
        component="market_data",
        trigger_statuses=("UNAVAILABLE", "STALE", "UNKNOWN"),
        severity=Severity.HIGH,
    ),
    AlertRule(
        rule_id="broker-health",
        component="broker_gateway",
        trigger_statuses=("UNAVAILABLE", "STALE", "UNKNOWN"),
        severity=Severity.HIGH,
    ),
)


class LiveOperationsService:
    """The control plane can contain risk; it cannot repair, resume, or trade."""

    def __init__(self, policy: EscalationPolicy | None = None) -> None:
        self.policy = policy or EscalationPolicy()

    def collect(self, *, now: datetime | None = None) -> OperationalSnapshot:
        at = now or _now()
        signals = self._signals(at)
        raised = tuple(self._raise_for(signal, at) for signal in signals if self._rule_for(signal))
        active_alerts = tuple(item for item in raised if item is not None)
        for item in active_alerts:
            self._open_or_update_incident(item, at)
        for item in active_alerts:
            if item.severity is Severity.CRITICAL:
                self._safe_response(item, at)
        snapshot = OperationalSnapshot(
            snapshot_id=f"ops-{sha256({'at': at.isoformat(), 'signals': [s.signal_id for s in signals]})[:12]}",
            captured_at=at,
            signals=signals,
            alerts=tuple(alerts()),
            incidents=tuple(incidents()),
            actions=tuple(actions()),
        )
        return put_snapshot(snapshot)

    def acknowledge(
        self, incident_id: str, *, actor_id: str, rationale: str, now: datetime | None = None
    ) -> Incident:
        return self._transition(
            incident_id, IncidentState.ACKNOWLEDGED, actor_id, rationale, (), now
        )

    def resolve(
        self,
        incident_id: str,
        *,
        actor_id: str,
        rationale: str,
        evidence: tuple[IncidentEvidence, ...],
        condition_persists: bool,
        now: datetime | None = None,
    ) -> Incident:
        if condition_persists:
            raise ValueError("cannot resolve or close while the critical condition persists")
        if not rationale or not evidence:
            raise ValueError("human resolution requires rationale and evidence")
        return self._transition(
            incident_id, IncidentState.RESOLVED, actor_id, rationale, evidence, now
        )

    def _signals(self, at: datetime) -> tuple[HealthSignal, ...]:
        from quantlab.broker_gateway.service import health as broker_health
        from quantlab.realtime_data.service import health as market_data_health
        from quantlab.reconciliation.repository import last as last_reconciliation
        from quantlab.restricted_execution.repository import list_submissions

        report = last_reconciliation()
        reconciliation = (
            "UNKNOWN"
            if report is None
            else ("MISMATCH" if "MISMATCH" in report.status.value else "HEALTHY")
        )
        gateway = (
            "UNKNOWN"
            if any(item.state.value == "SUBMISSION_UNKNOWN" for item in list_submissions())
            else "BLOCKED"
        )
        safety = "KILL_ACTIVE" if is_active(KillScope.GLOBAL) else "HEALTHY"
        data, data_detail, data_evidence = _market_data_signal(market_data_health)
        broker, broker_detail, broker_evidence = _broker_signal(broker_health)
        evidence = (sha256({"at": at.isoformat(), "gates": LiveSafetyGates().model_dump()}),)
        return (
            HealthSignal(
                signal_id="market-data",
                component="market_data",
                status=data,
                observed_at=at,
                evidence=evidence + data_evidence,
                detail=data_detail,
            ),
            HealthSignal(
                signal_id="broker-gateway",
                component="broker_gateway",
                status=broker,
                observed_at=at,
                evidence=evidence + broker_evidence,
                detail=broker_detail,
            ),
            HealthSignal(
                signal_id="reconciliation",
                component="reconciliation",
                status=reconciliation,
                observed_at=at,
                evidence=evidence,
                detail="latest reconciliation status",
            ),
            HealthSignal(
                signal_id="restricted-gateway",
                component="restricted_gateway",
                status=gateway,
                observed_at=at,
                evidence=evidence,
                detail="gateway remains disabled unless a test adapter is injected",
            ),
            HealthSignal(
                signal_id="safety",
                component="safety",
                status=safety,
                observed_at=at,
                evidence=evidence,
                detail="global safety state",
            ),
        )

    def _rule_for(self, signal: HealthSignal) -> AlertRule | None:
        return next(
            (
                rule
                for rule in _RULES
                if rule.component == signal.component and signal.status in rule.trigger_statuses
            ),
            None,
        )

    def _raise_for(self, signal: HealthSignal, at: datetime) -> AlertEvent | None:
        rule = self._rule_for(signal)
        if rule is None:
            return None
        fingerprint = sha256(
            {"rule": rule.rule_id, "status": signal.status, "component": signal.component}
        )
        previous = alert(fingerprint)
        if previous is None:
            return put_alert(
                AlertEvent(
                    alert_id=f"alert-{fingerprint[:12]}",
                    fingerprint=fingerprint,
                    rule_id=rule.rule_id,
                    severity=rule.severity,
                    status=signal.status,
                    first_seen_at=at,
                    last_seen_at=at,
                    evidence=signal.evidence,
                )
            )
        suppressed = (
            at - previous.last_seen_at
        ).total_seconds() < self.policy.notification_interval_seconds
        return put_alert(
            previous.model_copy(
                update={
                    "last_seen_at": at,
                    "occurrence_count": previous.occurrence_count + 1,
                    "notification_suppressed": suppressed,
                    "evidence": tuple(sorted(set(previous.evidence + signal.evidence))),
                }
            )
        )

    def _open_or_update_incident(self, item: AlertEvent, at: datetime) -> Incident:
        previous = incident(item.fingerprint)
        evidence = IncidentEvidence(
            evidence_id=f"evidence-{item.alert_id}",
            source="alert",
            content_hash=sha256(item.model_dump(mode="json")),
            observed_at=at,
            detail=item.status,
        )
        if previous is None:
            event = IncidentEvent(
                event_id=f"event-{item.alert_id}",
                incident_id=f"incident-{item.fingerprint[:12]}",
                from_state=None,
                to_state=IncidentState.DETECTED,
                actor_id="system",
                occurred_at=at,
                evidence_ids=(evidence.evidence_id,),
            )
            return put_incident(
                Incident(
                    incident_id=event.incident_id,
                    fingerprint=item.fingerprint,
                    severity=item.severity,
                    state=IncidentState.DETECTED,
                    opened_at=at,
                    updated_at=at,
                    alert_ids=(item.alert_id,),
                    evidence=(evidence,),
                    events=(event,),
                )
            )
        state = (
            IncidentState.REOPENED
            if previous.state in {IncidentState.RESOLVED, IncidentState.CLOSED}
            else previous.state
        )
        event = IncidentEvent(
            event_id=f"event-{item.alert_id}-{previous.events.__len__()}",
            incident_id=previous.incident_id,
            from_state=previous.state if state is IncidentState.REOPENED else None,
            to_state=state,
            actor_id="system",
            occurred_at=at,
            evidence_ids=(evidence.evidence_id,),
        )
        return put_incident(
            previous.model_copy(
                update={
                    "state": state,
                    "updated_at": at,
                    "alert_ids": tuple(sorted(set(previous.alert_ids + (item.alert_id,)))),
                    "evidence": previous.evidence + (evidence,),
                    "events": previous.events + (event,),
                }
            )
        )

    def _safe_response(self, item: AlertEvent, at: datetime) -> ResponseAction:
        key = f"{item.alert_id}:investigate"
        if self.policy.allow_automatic_kill_switch:
            key = f"{item.alert_id}:kill"
            if not is_active(KillScope.GLOBAL):
                activate(
                    KillScope.GLOBAL,
                    reason="live-ops critical incident",
                    created_by="live-ops",
                )
            return put_action(
                ResponseAction(
                    action_id=f"action-{key}",
                    kind=ResponseActionKind.ACTIVATE_KILL_SWITCH,
                    incident_id=f"incident-{item.fingerprint[:12]}",
                    requested_at=at,
                    actor_id="system",
                    idempotency_key=key,
                    verified=is_active(KillScope.GLOBAL),
                    detail="global kill switch requested; no automatic resume",
                )
            )
        return put_action(
            ResponseAction(
                action_id=f"action-{key}",
                kind=ResponseActionKind.REQUEST_INVESTIGATION,
                incident_id=f"incident-{item.fingerprint[:12]}",
                requested_at=at,
                actor_id="system",
                idempotency_key=key,
                verified=True,
                detail="human investigation requested; no automatic recovery",
            )
        )

    def _transition(
        self,
        incident_id: str,
        to_state: IncidentState,
        actor_id: str,
        rationale: str,
        new_evidence: tuple[IncidentEvidence, ...],
        now: datetime | None,
    ) -> Incident:
        item = incident_by_id(incident_id)
        if item is None:
            raise KeyError(incident_id)
        if not actor_id or actor_id.lower() in {"ai", "llm", "system"}:
            raise ValueError("AI and system actors cannot acknowledge or resolve incidents")
        at = now or _now()
        event = IncidentEvent(
            event_id=f"event-{incident_id}-{len(item.events)}",
            incident_id=incident_id,
            from_state=item.state,
            to_state=to_state,
            actor_id=actor_id,
            occurred_at=at,
            rationale=rationale,
            evidence_ids=tuple(row.evidence_id for row in new_evidence),
        )
        return put_incident(
            item.model_copy(
                update={
                    "state": to_state,
                    "updated_at": at,
                    "evidence": item.evidence + new_evidence,
                    "events": item.events + (event,),
                    "closure_rationale": rationale
                    if to_state in {IncidentState.RESOLVED, IncidentState.CLOSED}
                    else item.closure_rationale,
                }
            )
        )


def _market_data_signal(probe: object) -> tuple[str, str, tuple[str, ...]]:
    """Translate an observed feed health probe without inventing a healthy state."""
    try:
        result = probe()  # type: ignore[operator]
    except Exception as exc:
        return "UNKNOWN", f"market-data health probe failed: {exc}", ()
    overall = str(getattr(result, "overall", "unknown")).upper()
    mapping = {
        "HEALTHY": "HEALTHY",
        "STALE": "STALE",
        "DISCONNECTED": "UNAVAILABLE",
        "HALTED": "UNAVAILABLE",
        "DEGRADED": "UNAVAILABLE",
        "RECOVERING": "UNAVAILABLE",
    }
    status = mapping.get(overall, "UNKNOWN")
    return status, f"observed market-data health={overall}", (sha256(result.model_dump()),)


def _broker_signal(probe: object) -> tuple[str, str, tuple[str, ...]]:
    """Translate a read-only broker probe; unavailable is never silently healthy."""
    try:
        result = probe()  # type: ignore[operator]
    except Exception as exc:
        return "UNKNOWN", f"broker health probe failed: {exc}", ()
    if bool(getattr(result, "stale", False)):
        status = "STALE"
    elif bool(getattr(result, "healthy", False)):
        status = "HEALTHY"
    elif str(getattr(result, "state", "")).upper() == "DISCONNECTED":
        status = "UNAVAILABLE"
    else:
        status = "UNKNOWN"
    return (
        status,
        f"observed broker state={getattr(result, 'state', 'unknown')}",
        (sha256(result.model_dump()),),
    )
