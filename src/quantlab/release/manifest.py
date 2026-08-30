"""Immutable hashed certification package and release manifest."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from quantlab import __version__
from quantlab.data.fabric.checksums import sha256_bytes
from quantlab.release.models import (
    CertificationPackage,
    CertificationRequest,
    ReleaseManifest,
    ReleaseStage,
)


def package_hash(request: CertificationRequest) -> str:
    material = (
        f"{request.package_id}|{request.spec_hash}|{request.data_kind}|"
        f"{request.intended_stage.value}|{request.owner_id}|{request.validator_id}|"
        f"{request.max_capital}|{request.as_of.isoformat()}"
    )
    return sha256_bytes(material.encode())


def mint_package(request: CertificationRequest) -> CertificationPackage:
    digest = package_hash(request)
    return CertificationPackage(
        package_id=request.package_id,
        spec_hash=request.spec_hash,
        evidence_hash=digest,
        software_version=__version__,
        data_kind=request.data_kind,
        intended_stage=request.intended_stage,
        owner_id=request.owner_id,
        validator_id=request.validator_id,
        created_at=request.as_of,
        expires_at=request.as_of + timedelta(days=30),
        package_hash=digest,
    )


def mint_manifest(request: CertificationRequest, *, release_id: str) -> ReleaseManifest:
    pkg = mint_package(request)
    payload = (
        f"{release_id}|{pkg.package_id}|{pkg.package_hash}|{request.max_capital}|"
        f"{request.intended_stage.value}|{request.validator_id}"
    )
    digest = sha256_bytes(payload.encode())
    return ReleaseManifest(
        release_id=release_id,
        certification_id=pkg.package_id,
        software_version=__version__,
        git_commit="",
        configuration_hash=request.spec_hash,
        research_snapshot_hash=request.spec_hash,
        data_snapshot_hash=request.spec_hash,
        model_hash=request.spec_hash,
        ensemble_hash=request.spec_hash,
        portfolio_policy_hash="port-v1",
        risk_policy_hash="risk-v1",
        execution_policy_hash="exec-v1",
        safety_policy_hash="safety-policy-v1",
        ops_health_hash="ops-v1",
        capital_limit=request.max_capital,
        release_stage=request.intended_stage
        if request.intended_stage is not ReleaseStage.EXPANDED_LIVE
        else ReleaseStage.SHADOW,
        expiry=datetime(2024, 2, 1, tzinfo=UTC),
        approved_by=request.human_approver_id,
        validator=request.validator_id,
        timestamp=request.as_of,
        manifest_hash=digest,
        live_trading=False,
        live_enabled=False,
    )
