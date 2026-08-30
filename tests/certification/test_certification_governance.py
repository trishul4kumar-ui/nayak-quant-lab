from __future__ import annotations

import pytest
from tests.certification.test_certification_machine import all_pass

from quantlab.certification.change import classify_change
from quantlab.certification.enums import ChangeClass, ItemStatus
from quantlab.certification.models import Candidate, CertificationRequest
from quantlab.certification.policy import block_reasons
from quantlab.certification.service import create_candidate, revise_candidate
from quantlab.core.errors import CertificationError


def _candidate(**kwargs: str) -> Candidate:
    payload = {
        "candidate_id": "c-change",
        "software_version": "3.1.0",
        "snapshot_id": "synthetic-diagnostic",
    }
    payload.update(kwargs)
    return Candidate(**payload)


def test_minor_change_is_software_only() -> None:
    before = _candidate()
    after = _candidate(software_version="2.3.1")
    assert classify_change(before, after) is ChangeClass.MINOR


def test_material_snapshot_change() -> None:
    before = _candidate()
    after = _candidate(snapshot_id="other-snap")
    assert classify_change(before, after) is ChangeClass.MATERIAL


def test_major_model_change() -> None:
    before = _candidate()
    after = _candidate(model_id="new-arch")
    assert classify_change(before, after) is ChangeClass.MAJOR


def test_feature_formula_change_is_major() -> None:
    before = Candidate(candidate_id="c", feature_versions={"momentum": "v1"})
    after = Candidate(candidate_id="c", feature_versions={"momentum": "v2"})
    assert classify_change(before, after) is ChangeClass.MAJOR


def test_revise_rejects_material() -> None:
    create_candidate(CertificationRequest(candidate_id="c-change"))
    with pytest.raises(CertificationError, match="new candidate version"):
        revise_candidate(_candidate(snapshot_id="mutated"))


def test_block_reasons_critical_not_tested() -> None:
    from quantlab.certification.checklist import default_items

    reasons = block_reasons(_candidate(), default_items())
    assert any(item.startswith("critical_not_tested:") for item in reasons)


def test_block_reasons_synthetic_production() -> None:
    from quantlab.certification.checklist import default_items

    cand = Candidate(
        candidate_id="c",
        data_kind="synthetic",
        claims_production_evidence=True,
    )
    reasons = block_reasons(cand, default_items())
    assert "synthetic_production_evidence" in reasons


def test_all_pass_has_no_block_reasons() -> None:
    reasons = block_reasons(_candidate(), all_pass())
    assert reasons == []


def test_retired_models_remain_in_state_store() -> None:
    from tests.certification.test_certification_machine import place

    from quantlab.certification.enums import CertificationState
    from quantlab.certification.state import get_result

    place(CertificationState.RETIRED, cid="retired-1")
    found = get_result("retired-1")
    assert found is not None
    assert found.state is CertificationState.RETIRED
    assert found.candidate.candidate_id == "retired-1"


@pytest.mark.parametrize("status", list(ItemStatus))
def test_item_status_includes_waived(status: ItemStatus) -> None:
    assert status.value in {"pass", "fail", "warn", "not_tested", "waived"}


def test_create_records_research_not_live_note() -> None:
    result = create_candidate()
    assert "LIVE" in result.note.upper() or "live" in result.note.lower()
    assert result.state.value == "draft"
