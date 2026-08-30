from __future__ import annotations

from datetime import UTC, datetime

import pytest

from quantlab import __version__
from quantlab.core.config import LiveSafetyGates
from quantlab.release.errors import CertificationBlocked, ReleaseWaiverError
from quantlab.release.models import ActorKind, ReleaseStage, WaiverRecord
from quantlab.release.service import (
    add_waiver,
    approve,
    certify,
    default_passing_request,
    evaluate,
    expire,
    revoke,
)
from quantlab.release.state import CertState, current, force

pytestmark = pytest.mark.release


def test_version_and_live_off() -> None:
    assert __version__ == "3.1.0"
    assert LiveSafetyGates().live_trading is False
    assert LiveSafetyGates().broker_write_enabled is False


def test_default_evaluate_blocks_certification() -> None:
    result = evaluate()
    assert result.live_trading is False
    assert result.live_enabled is False
    assert result.broker_connected is False
    assert any(item.blocks for item in result.criteria)
    with pytest.raises(CertificationBlocked):
        certify()


def test_independent_validation_required() -> None:
    request = default_passing_request().model_copy(
        update={"independent_validation": False, "validator_id": ""}
    )
    with pytest.raises(CertificationBlocked):
        certify(request)


def test_ai_cannot_certify() -> None:
    request = default_passing_request().model_copy(update={"actor": ActorKind.AI_SUGGESTION})
    with pytest.raises(CertificationBlocked):
        certify(request)


def test_safety_cannot_be_waived() -> None:
    with pytest.raises(ReleaseWaiverError):
        add_waiver(
            WaiverRecord(
                waiver_id="w1",
                criterion_id="safety_readiness",
                reason="bypass",
                risk_statement="none",
                authority="authority-1",
                scope="safety",
                created_at=datetime(2024, 1, 2, tzinfo=UTC),
                expires_at=datetime(2024, 2, 1, tzinfo=UTC),
                mitigation="none",
            )
        )


def test_synthetic_cannot_certify_restricted_live() -> None:
    request = default_passing_request().model_copy(
        update={"intended_stage": ReleaseStage.RESTRICTED_LIVE}
    )
    with pytest.raises(CertificationBlocked):
        certify(request)


def test_research_package_can_certify_without_live() -> None:
    result = certify(default_passing_request())
    assert result.state is CertState.CERTIFIED
    assert result.live_enabled is False
    assert result.live_trading is False
    assert LiveSafetyGates().live_trading is False


def test_human_approval_cannot_bypass_fail() -> None:
    request = default_passing_request().model_copy(update={"recon_break": True})
    with pytest.raises(CertificationBlocked):
        approve(request)


def test_separation_of_duties() -> None:
    request = default_passing_request().model_copy(update={"human_approver_id": "researcher-1"})
    certify(default_passing_request())
    with pytest.raises(CertificationBlocked):
        approve(request)


def test_release_eligible_is_not_live() -> None:
    certify(default_passing_request())
    result = approve(default_passing_request())
    assert result.state is CertState.RELEASE_ELIGIBLE
    assert result.live_enabled is False
    assert result.manifest is not None
    assert result.manifest.live_enabled is False


def test_material_mutation_blocks() -> None:
    request = default_passing_request().model_copy(update={"model_mutated": True})
    with pytest.raises(CertificationBlocked):
        certify(request)


def test_expired_and_revoked_are_not_live() -> None:
    certify(default_passing_request())
    expired = expire()
    assert expired.state is CertState.EXPIRED
    assert expired.live_enabled is False
    force(CertState.CERTIFIED)
    revoked = revoke()
    assert revoked.state is CertState.REVOKED
    assert current() is CertState.REVOKED


def test_deterministic_package_hash() -> None:
    first = evaluate(default_passing_request())
    second = evaluate(default_passing_request())
    assert first.package is not None
    assert second.package is not None
    assert first.package.package_hash == second.package.package_hash
