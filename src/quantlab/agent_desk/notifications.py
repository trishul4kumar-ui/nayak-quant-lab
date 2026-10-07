"""Deduplicated, non-modal desk notifications."""

from __future__ import annotations

from datetime import datetime

from quantlab.agent_desk.models import DeskNotification, NotificationSeverity
from quantlab.trade_candidates.models import CandidateStatus, TradeCandidatePacket


def candidate_notification(
    candidate: TradeCandidatePacket,
    *,
    now: datetime,
    existing: tuple[DeskNotification, ...],
) -> DeskNotification | None:
    """Only fresh validated candidates can request human review; duplicates are suppressed."""
    if candidate.status is not CandidateStatus.READY_FOR_REVIEW or candidate.expires_at <= now:
        return None
    dedupe_key = f"candidate-review:{candidate.content_hash}"
    if any(item.dedupe_key == dedupe_key and not item.acknowledged for item in existing):
        return None
    return DeskNotification(
        created_at=now,
        schema_version="daily-desk-v1",
        notification_id=dedupe_key,
        severity=NotificationSeverity.ACTION_REQUIRED,
        title="Candidate review required",
        body=f"{candidate.security_id} is ready for research review; no order is created.",
        candidate_hash=candidate.content_hash,
        dedupe_key=dedupe_key,
    )
