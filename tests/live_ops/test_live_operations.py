from __future__ import annotations

from datetime import UTC, datetime

import pytest

from quantlab.live_ops.models import AlertEvent, EscalationPolicy, IncidentEvidence, Severity
from quantlab.live_ops.repository import alerts, incidents, reset_for_tests
from quantlab.live_ops.service import LiveOperationsService
from quantlab.realtime_data.hashing import sha256
from quantlab.realtime_data.service import reset_for_tests as reset_market_data
from quantlab.realtime_data.service import snapshot as market_snapshot


def test_collection_deduplicates_alerts_and_keeps_evidence() -> None:
    reset_for_tests()
    service = LiveOperationsService()
    now = datetime(2026, 1, 2, tzinfo=UTC)
    service.collect(now=now)
    service.collect(now=now)

    assert alerts()
    assert any(item.occurrence_count == 2 for item in alerts())
    assert incidents()


def test_market_data_signal_uses_the_observed_feed_health() -> None:
    reset_for_tests()
    reset_market_data()
    market_snapshot()
    snapshot = LiveOperationsService().collect(now=datetime(2026, 1, 2, tzinfo=UTC))
    market = next(item for item in snapshot.signals if item.signal_id == "market-data")
    assert market.status == "HEALTHY"
    assert "observed market-data health=HEALTHY" in market.detail


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
