"""Immutable hashed execution authorization. Not a broker submit."""

from __future__ import annotations

from datetime import UTC, timedelta

from quantlab.data.fabric.checksums import sha256_bytes
from quantlab.safety.models import ExecutionAuthorization, SafetyRequest


def authorization_hash(request: SafetyRequest, *, authorization_id: str) -> str:
    material = (
        f"{authorization_id}|{request.decision_hash}|{request.target_portfolio_hash}|"
        f"{request.order_plan_hash}|{request.certification_id}|{request.shadow_cycle_id}|"
        f"{request.market_snapshot_hash}|{request.account_state_hash}|{request.policy_id}|"
        f"{request.account_id}|{request.nonce}|{request.as_of.isoformat()}"
    )
    return sha256_bytes(material.encode())


def mint(request: SafetyRequest, *, authorization_id: str) -> ExecutionAuthorization:
    digest = authorization_hash(request, authorization_id=authorization_id)
    return ExecutionAuthorization(
        authorization_id=authorization_id,
        decision_hash=request.decision_hash,
        target_portfolio_hash=request.target_portfolio_hash,
        order_plan_hash=request.order_plan_hash,
        paper_evidence_id=request.paper_evidence_id,
        shadow_evidence_id=request.shadow_cycle_id,
        certification_id=request.certification_id,
        risk_snapshot_ref=request.risk_state,
        data_snapshot_ref=request.market_snapshot_hash,
        tca_policy_ref=request.tca_policy_id,
        account_identity=request.account_id,
        execution_policy_identity=request.policy_id,
        system_state="live_disabled",
        created_at=request.as_of,
        expires_at=request.as_of + timedelta(minutes=5),
        version="1",
        nonce=request.nonce,
        authorization_hash=digest,
        live_release=False,
        release_allowed=False,
        actor=request.actor,
    )


def still_valid(auth: ExecutionAuthorization, request: SafetyRequest) -> bool:
    if request.mutated_authorization:
        return False
    if request.as_of > auth.expires_at.replace(tzinfo=UTC):
        return False
    return auth.authorization_hash == authorization_hash(
        request, authorization_id=auth.authorization_id
    )
