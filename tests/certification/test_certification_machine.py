from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from quantlab.certification.checklist import CRITICAL_CODES, apply_waiver, default_items
from quantlab.certification.enums import (
    CertificationState,
    ChecklistCode,
    ItemStatus,
    ReviewerRole,
    SuspensionReason,
)
from quantlab.certification.machine import allowed_targets, assert_transition
from quantlab.certification.models import (
    CertificationRequest,
    ChecklistItem,
    Waiver,
)
from quantlab.certification.service import (
    certify,
    create_candidate,
    run_validation,
    suspend,
    transition,
)
from quantlab.core.errors import IllegalCertificationTransition, WaiverError


def all_pass() -> list[ChecklistItem]:
    return [
        ChecklistItem(
            code=code,
            status=ItemStatus.PASS,
            evidence_id="fixture",
            critical=code in CRITICAL_CODES,
            note="test fixture; not production evidence",
        )
        for code in ChecklistCode
    ]


def _fail_survivorship() -> list[ChecklistItem]:
    rows = []
    for item in all_pass():
        if item.code is ChecklistCode.SURVIVORSHIP:
            rows.append(item.model_copy(update={"status": ItemStatus.FAIL}))
        else:
            rows.append(item)
    return rows


def place(state: CertificationState, *, cid: str = "c1") -> None:
    items = all_pass()
    create_candidate(CertificationRequest(candidate_id=cid, checklist=items))
    if state is CertificationState.DRAFT:
        return
    if state is CertificationState.UNDER_VALIDATION:
        transition(cid, CertificationState.UNDER_VALIDATION)
        return
    if state is CertificationState.VALIDATION_FAILED:
        run_validation(cid, CertificationRequest(candidate_id=cid, checklist=_fail_survivorship()))
        return
    run_validation(cid, CertificationRequest(candidate_id=cid, checklist=items))
    path: list[CertificationState] = []
    if state in {
        CertificationState.VALIDATION_PASSED,
        CertificationState.PAPER_ELIGIBLE,
        CertificationState.PAPER_ACTIVE,
        CertificationState.PAPER_FAILED,
        CertificationState.SHADOW_ELIGIBLE,
        CertificationState.SHADOW_ACTIVE,
        CertificationState.PRELIVE_REVIEW,
        CertificationState.CERTIFIED,
        CertificationState.SUSPENDED,
        CertificationState.RETIRED,
    }:
        if state is CertificationState.VALIDATION_PASSED:
            return
        path.append(CertificationState.PAPER_ELIGIBLE)
        if state is CertificationState.PAPER_ELIGIBLE:
            transition(cid, CertificationState.PAPER_ELIGIBLE)
            return
        if state is CertificationState.SUSPENDED:
            transition(cid, CertificationState.PAPER_ELIGIBLE)
            suspend(cid, SuspensionReason.VALIDATION_EXPIRY)
            return
        if state is CertificationState.RETIRED:
            from quantlab.certification.service import retire

            transition(cid, CertificationState.PAPER_ELIGIBLE)
            retire(cid)
            return
        if state is CertificationState.PAPER_FAILED:
            transition(cid, CertificationState.PAPER_ELIGIBLE)
            transition(cid, CertificationState.PAPER_ACTIVE)
            transition(cid, CertificationState.PAPER_FAILED)
            return
        transition(cid, CertificationState.PAPER_ELIGIBLE)
        transition(cid, CertificationState.PAPER_ACTIVE)
        if state is CertificationState.PAPER_ACTIVE:
            return
        transition(cid, CertificationState.SHADOW_ELIGIBLE)
        if state is CertificationState.SHADOW_ELIGIBLE:
            return
        transition(cid, CertificationState.SHADOW_ACTIVE)
        if state is CertificationState.SHADOW_ACTIVE:
            return
        transition(cid, CertificationState.PRELIVE_REVIEW)
        if state is CertificationState.PRELIVE_REVIEW:
            return
        certify(
            cid,
            request=CertificationRequest(
                candidate_id=cid,
                role=ReviewerRole.CERTIFICATION_REVIEWER,
            ),
        )


_ILLEGAL = [
    (current, target)
    for current in CertificationState
    for target in CertificationState
    if target is not current and target not in allowed_targets(current)
]


@pytest.mark.parametrize(("current", "target"), _ILLEGAL)
def test_illegal_transition_raises(
    current: CertificationState,
    target: CertificationState,
) -> None:
    place(current)
    with pytest.raises(IllegalCertificationTransition):
        transition("c1", target)


def test_draft_to_certified_is_illegal() -> None:
    create_candidate(CertificationRequest(candidate_id="c1", checklist=all_pass()))
    with pytest.raises(IllegalCertificationTransition):
        transition("c1", CertificationState.CERTIFIED)
    with pytest.raises(IllegalCertificationTransition):
        certify(
            "c1",
            request=CertificationRequest(
                candidate_id="c1",
                role=ReviewerRole.CERTIFICATION_REVIEWER,
            ),
        )


def test_assert_transition_draft_certified() -> None:
    with pytest.raises(IllegalCertificationTransition):
        assert_transition(CertificationState.DRAFT, CertificationState.CERTIFIED)


@pytest.mark.parametrize("state", list(CertificationState))
def test_allowed_targets_never_include_live(state: CertificationState) -> None:
    for target in allowed_targets(state):
        assert target.value != "live"
        assert "live_trading" not in target.value


def test_legal_happy_path_to_certified() -> None:
    place(CertificationState.CERTIFIED)
    from quantlab.certification.state import last_result

    result = last_result()
    assert result is not None
    assert result.state is CertificationState.CERTIFIED
    assert result.live_trading is False


def test_waiver_requires_authority() -> None:
    item = default_items()[0]
    with pytest.raises(WaiverError):
        apply_waiver(
            item,
            Waiver(
                waiver_id="",
                reason="",
                authority="",
                timestamp=datetime(2024, 1, 1, tzinfo=UTC),
                scope="",
                expiry=datetime(2024, 1, 2, tzinfo=UTC),
            ),
        )


def test_safety_cannot_be_waived() -> None:
    item = next(row for row in default_items() if row.code is ChecklistCode.SAFETY)
    with pytest.raises(WaiverError, match="SAFETY"):
        apply_waiver(
            item,
            Waiver(
                waiver_id="W1",
                reason="ops",
                authority="CRO",
                timestamp=datetime(2024, 1, 1, tzinfo=UTC),
                scope="safety",
                expiry=datetime(2024, 6, 1, tzinfo=UTC),
            ),
        )


def test_complete_waiver_marks_waived() -> None:
    item = next(row for row in default_items() if row.code is ChecklistCode.SURVIVORSHIP)
    waived = apply_waiver(
        item,
        Waiver(
            waiver_id="W1",
            reason="documented exception",
            authority="DATA_REVIEWER",
            timestamp=datetime(2024, 1, 1, tzinfo=UTC),
            scope="survivorship",
            expiry=datetime(2024, 6, 1, tzinfo=UTC),
        ),
    )
    assert waived.status is ItemStatus.WAIVED
    assert waived.waiver is not None


def test_waiver_expiry_must_follow_timestamp() -> None:
    item = next(row for row in default_items() if row.code is ChecklistCode.TCA)
    stamp = datetime(2024, 1, 2, tzinfo=UTC)
    with pytest.raises(WaiverError):
        apply_waiver(
            item,
            Waiver(
                waiver_id="W1",
                reason="x",
                authority="a",
                timestamp=stamp,
                scope="tca",
                expiry=stamp - timedelta(days=1),
            ),
        )


@pytest.mark.parametrize("reason", list(SuspensionReason))
def test_suspension_reason_is_explicit(reason: SuspensionReason) -> None:
    assert reason.value
    assert reason.value != "live"


@pytest.mark.parametrize("role", list(ReviewerRole))
def test_roles_are_logical(role: ReviewerRole) -> None:
    assert role.value
    assert "broker" not in role.value
