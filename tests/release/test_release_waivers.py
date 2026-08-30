from __future__ import annotations

from datetime import UTC, datetime

import pytest

from quantlab.release.errors import ReleaseWaiverError
from quantlab.release.models import ActorKind, WaiverRecord
from quantlab.release.waivers import record

pytestmark = pytest.mark.release


def test_expired_waiver_rejected() -> None:
    with pytest.raises(ReleaseWaiverError):
        record(
            WaiverRecord(
                waiver_id="w-exp",
                criterion_id="execution_readiness",
                reason="late",
                risk_statement="risk",
                authority="authority-1",
                scope="execution",
                created_at=datetime(2024, 1, 1, tzinfo=UTC),
                expires_at=datetime(2024, 1, 1, tzinfo=UTC),
                mitigation="none",
            )
        )


def test_ai_cannot_waive() -> None:
    with pytest.raises(ReleaseWaiverError):
        record(
            WaiverRecord(
                waiver_id="w-ai",
                criterion_id="execution_readiness",
                reason="ai",
                risk_statement="risk",
                authority="ai",
                scope="execution",
                created_at=datetime(2024, 1, 2, tzinfo=UTC),
                expires_at=datetime(2024, 2, 1, tzinfo=UTC),
                mitigation="none",
                actor=ActorKind.AI_SUGGESTION,
            )
        )
