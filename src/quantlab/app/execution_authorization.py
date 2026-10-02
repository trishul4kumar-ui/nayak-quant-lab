"""Qt-safe execution eligibility presentation. It never approves or routes orders."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from quantlab.execution_authorization.models import AuthorizationScope
from quantlab.execution_authorization.repository import last_assessment
from quantlab.execution_authorization.service import assess

_LAST: dict[str, Any] | None = None


def run_payload() -> dict[str, Any]:
    now = datetime.now(tz=UTC)
    scope = AuthorizationScope(
        deployment_id="unconfigured",
        broker_account_fingerprint="",
        allowed_security_ids=(),
        universe_version="",
        strategy_hash="",
        model_hash="",
        portfolio_policy_hash="",
        release_id="",
        data_provider="",
        data_policy_hash="",
        risk_policy_hash="",
        max_gross_exposure=None,
        max_notional=None,
        max_turnover=None,
        operating_mode="restricted_live_review",
        session_start=now,
        session_end=now + timedelta(minutes=1),
        expiry=now + timedelta(minutes=2),
    )
    item = assess(scope)
    payload = item.model_dump(mode="json")
    global _LAST
    _LAST = payload
    return payload


def last_run_row() -> dict[str, Any] | None:
    return _LAST


def status_payload() -> dict[str, Any]:
    item = last_assessment()
    return {
        "state": item.state.value if item else "INELIGIBLE",
        "blockers": list(item.blockers) if item else ["assessment_missing"],
        "live_trading": False,
        "broker_write_enabled": False,
    }
