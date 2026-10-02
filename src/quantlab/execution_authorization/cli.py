"""Explicitly human-confirmed execution-eligibility CLI. It never opens a broker route."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from typing import Any

from quantlab.execution_authorization.models import AuthorizationScope
from quantlab.execution_authorization.repository import audit, last_assessment
from quantlab.execution_authorization.service import approve, assess, revoke


def add_execution_authorization_parser(sub: Any) -> None:
    parser = sub.add_parser(
        "execution-auth", help="restricted-live eligibility; no broker execution"
    )
    cmd = parser.add_subparsers(dest="execution_auth_cmd", required=True)
    cmd.add_parser("assess", help="fail-closed eligibility assessment")
    cmd.add_parser("package", help="show the latest immutable assessment package")
    cmd.add_parser("status", help="show eligibility status")
    approve_parser = cmd.add_parser(
        "approve", help="record explicit human review of an eligible package"
    )
    approve_parser.add_argument("--approver", required=True)
    approve_parser.add_argument("--confirm", required=True)
    revoke_parser = cmd.add_parser("revoke", help="revoke a specific human approval")
    revoke_parser.add_argument("approval_id")
    revoke_parser.add_argument("--reason", required=True)
    revoke_parser.add_argument("--actor", required=True)
    cmd.add_parser("audit", help="authorization audit history")


def run_execution_authorization_command(args: Any) -> int:
    command = args.execution_auth_cmd
    if command == "assess":
        payload: object = assess(_default_scope()).model_dump(mode="json")
    elif command == "package":
        item = last_assessment()
        payload = item.model_dump(mode="json") if item else {"note": "No assessment."}
    elif command == "status":
        item = last_assessment()
        payload = {"state": item.state.value if item else "INELIGIBLE", "live_trading": False}
    elif command == "approve":
        item = last_assessment()
        if item is None:
            raise SystemExit("no assessment; run execution-auth assess first")
        payload = approve(item, approver_id=args.approver, confirmation=args.confirm).model_dump(
            mode="json"
        )
    elif command == "revoke":
        payload = revoke(args.approval_id, reason=args.reason, revoked_by=args.actor).model_dump(
            mode="json"
        )
    else:
        payload = audit()
    print(json.dumps(payload, indent=2, default=str))
    return 0


def _default_scope() -> AuthorizationScope:
    now = datetime.now(tz=UTC)
    return AuthorizationScope(
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
