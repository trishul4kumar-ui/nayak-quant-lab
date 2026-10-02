from __future__ import annotations

from datetime import UTC, datetime

import pytest

from quantlab.live_ops.models import AlertEvent, EscalationPolicy, IncidentEvidence, Severity
from quantlab.live_ops.repository import alerts, incidents, reset_for_tests
from quantlab.live_ops.service import LiveOperationsService
from quantlab.realtime_data.hashing import sha256


def test_collection_deduplicates_alerts_and_keeps_evidence() -> None:
    reset_for_tests()
    service = LiveOperationsService()
    now = datetime(2026, 1, 2, tzinfo=UTC)
    service.collect(now=now)
    service.collect(now=now)

    assert alerts()
    assert any(item.occurrence_count == 2 for item in alerts())
    assert incidents()


def test_critical_response_is_idempotent_and_never_resumes() -> None:
    reset_for_tests()
    now = datetime(2026, 1, 2, tzinfo=UTC)
    service = LiveOperationsService(EscalationPolicy(allow_automatic_kill_switch=True))
    event = AlertEvent(
        alert_id="critical-alert",
        fingerprint=sha256("critical"),
        rule_id="test",
        severity=Severity.CRITICAL,
        status="FAILED",
        first_seen_at=now,
        last_seen_at=now,
    )
    first = service._safe_response(event, now)
    second = service._safe_response(event, now)

    assert first.action_id == second.action_id
    assert first.verified is True


def test_ai_cannot_close_incident() -> None:
    reset_for_tests()
    service = LiveOperationsService()
    now = datetime(2026, 1, 2, tzinfo=UTC)
    snapshot = service.collect(now=now)
    incident = snapshot.incidents[0]
    evidence = IncidentEvidence(
        evidence_id="evidence",
        source="human",
        content_hash=sha256("evidence"),
        observed_at=now,
    )
    with pytest.raises(ValueError, match="AI"):
        service.resolve(
            incident.incident_id,
            actor_id="ai",
            rationale="no",
            evidence=(evidence,),
            condition_persists=False,
            now=now,
        )
