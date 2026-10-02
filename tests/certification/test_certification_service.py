from __future__ import annotations

from pathlib import Path

import pytest
from tests.certification.test_certification_machine import all_pass, place

from quantlab import __version__
from quantlab.certification.checklist import CRITICAL_CODES
from quantlab.certification.enums import (
    CertificationState,
    ChecklistCode,
    ItemStatus,
    ReviewerRole,
    RiskCategory,
)
from quantlab.certification.models import CertificationRequest
from quantlab.certification.service import (
    certify,
    create_candidate,
    diff_candidates,
    reproduce_candidate,
    run_certification,
    run_validation,
)
from quantlab.core.config import LiveSafetyGates
from quantlab.core.errors import CertificationError, ReproductionBreak, SafetyError
from quantlab.knowledge.entities import NodeType
from quantlab.knowledge.graph import KnowledgeGraph
from quantlab.knowledge.ingest import ingest_certification


def test_version() -> None:
    assert __version__ == "3.1.0"


def test_live_trading_remains_false() -> None:
    assert LiveSafetyGates().live_trading is False
    result = create_candidate()
    assert result.live_trading is False
    assert result.run.live_trading is False
    assert result.state is CertificationState.DRAFT


def test_live_request_raises() -> None:
    with pytest.raises(SafetyError):
        create_candidate(CertificationRequest(live_trading=True))


def test_ai_override_raises() -> None:
    with pytest.raises(CertificationError, match="ai_certification_override"):
        create_candidate(CertificationRequest(ai_override=True))


def test_run_wraps_missing_evidence_as_not_tested() -> None:
    result = run_certification()
    by_code = {item.code: item.status for item in result.checklist}
    assert by_code[ChecklistCode.PAPER_RECONCILIATION] is ItemStatus.NOT_TESTED
    assert result.state in {
        CertificationState.VALIDATION_PASSED,
        CertificationState.VALIDATION_FAILED,
    }
    assert result.live_trading is False


def test_critical_not_tested_blocks_certify() -> None:
    from quantlab.certification.service import transition

    create_candidate(CertificationRequest(candidate_id="crit"))
    run_validation("crit")
    current = "crit"
    transition(current, CertificationState.PAPER_ELIGIBLE)
    transition(current, CertificationState.PAPER_ACTIVE)
    transition(current, CertificationState.SHADOW_ELIGIBLE)
    transition(current, CertificationState.SHADOW_ACTIVE)
    transition(current, CertificationState.PRELIVE_REVIEW)
    with pytest.raises(CertificationError, match="critical_not_tested"):
        certify(
            current,
            request=CertificationRequest(
                candidate_id=current,
                role=ReviewerRole.CERTIFICATION_REVIEWER,
            ),
        )


def test_synthetic_production_evidence_blocks() -> None:
    items = all_pass()
    create_candidate(
        CertificationRequest(
            candidate_id="syn",
            checklist=items,
            claims_production_evidence=True,
            data_kind="synthetic",
        )
    )
    run_validation(
        "syn",
        CertificationRequest(
            candidate_id="syn",
            checklist=items,
            claims_production_evidence=True,
            data_kind="synthetic",
        ),
    )
    from quantlab.certification.service import transition

    transition("syn", CertificationState.PAPER_ELIGIBLE)
    transition("syn", CertificationState.PAPER_ACTIVE)
    transition("syn", CertificationState.SHADOW_ELIGIBLE)
    transition("syn", CertificationState.SHADOW_ACTIVE)
    transition("syn", CertificationState.PRELIVE_REVIEW)
    with pytest.raises(CertificationError, match="synthetic_production_evidence"):
        certify(
            "syn",
            request=CertificationRequest(
                candidate_id="syn",
                role=ReviewerRole.CERTIFICATION_REVIEWER,
                claims_production_evidence=True,
                data_kind="synthetic",
            ),
        )


def test_certify_requires_certification_reviewer() -> None:
    place(CertificationState.PRELIVE_REVIEW, cid="role")
    with pytest.raises(CertificationError, match="CERTIFICATION_REVIEWER"):
        certify(
            "role",
            request=CertificationRequest(
                candidate_id="role",
                role=ReviewerRole.RESEARCHER,
            ),
        )


def test_reproduction_matches_frozen_hash() -> None:
    place(CertificationState.VALIDATION_PASSED, cid="repro")
    result = reproduce_candidate("repro")
    assert result.reproduction is not None
    assert result.reproduction.matched is True


def test_reproduction_break_on_wrong_hash() -> None:
    from quantlab.certification.reproduction import reproduce
    from quantlab.certification.state import get_result

    place(CertificationState.VALIDATION_PASSED, cid="brk")
    current = get_result("brk")
    assert current is not None
    with pytest.raises(ReproductionBreak):
        reproduce(current.candidate, current.checklist, expected_hash="deadbeef")


def test_future_payload_ignored_does_not_change_identity() -> None:
    a = create_candidate(CertificationRequest(candidate_id="fp", future_payload_ignored={}))
    b = create_candidate(CertificationRequest(candidate_id="fp", future_payload_ignored={"x": "y"}))
    assert a.run.certification_id == b.run.certification_id


def test_knowledge_ingest() -> None:
    result = create_candidate(CertificationRequest(candidate_id="kg"))
    graph = KnowledgeGraph(graph_id="kg-cert")
    ingest_certification(graph, result)
    types = {node.node_type for node in graph.nodes}
    assert NodeType.CERTIFICATION_CANDIDATE in types
    assert NodeType.VALIDATION_RUN in types
    assert NodeType.CERTIFICATION_DECISION in types
    assert NodeType.MODEL_RISK_ASSESSMENT in types


def test_ledger_optional_fields(tmp_path: Path) -> None:
    from quantlab.certification.experiment import run_certification_experiment

    result, row = run_certification_experiment(ledger_path=tmp_path / "ledger.json")
    assert row.certification_id == result.run.certification_id
    assert row.candidate_id == result.candidate.candidate_id
    assert row.certification_state == result.state.value
    assert row.application_version == "3.1.0"


def test_diff_two_candidates() -> None:
    create_candidate(CertificationRequest(candidate_id="d1"))
    create_candidate(CertificationRequest(candidate_id="d2"))
    payload = diff_candidates("d1", "d2")
    assert payload["change_class"] in {"minor", "material", "major"}
    assert payload["live_trading"] == "false"


def test_no_broker_imports() -> None:
    root = Path(__file__).resolve().parents[2] / "src" / "quantlab" / "certification"
    forbidden = ("kiteconnect", "zerodha", "openalgo", "quantlab.brokers")
    for path in root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in text, f"{token} in {path}"


@pytest.mark.parametrize("code", list(ChecklistCode))
def test_default_checklist_starts_not_tested(code: ChecklistCode) -> None:
    from quantlab.certification.checklist import default_items

    items = {item.code: item for item in default_items()}
    assert items[code].status is ItemStatus.NOT_TESTED
    if code in CRITICAL_CODES:
        assert items[code].critical is True


@pytest.mark.parametrize("category", list(RiskCategory))
def test_risk_taxonomy_has_no_hidden_low(category: RiskCategory) -> None:
    result = create_candidate(CertificationRequest(candidate_id="risk"))
    found = next(item for item in result.risks if item.category is category)
    assert found.severity.value
    assert found.note


def test_paper_wrap_marks_reconciliation(tmp_path: Path) -> None:
    from quantlab.paper_oms.library import seed_account, seed_decision, seed_snapshot, seed_target
    from quantlab.paper_oms.models import PaperOMSRequest
    from quantlab.paper_oms.service import run_paper_oms

    run_paper_oms(
        PaperOMSRequest(),
        decision=seed_decision(),
        target=seed_target(),
        account=seed_account(),
        snapshot=seed_snapshot(),
    )
    result = run_certification(CertificationRequest(candidate_id="paper-wrap"))
    recon = next(
        item for item in result.checklist if item.code is ChecklistCode.PAPER_RECONCILIATION
    )
    assert recon.status in {ItemStatus.PASS, ItemStatus.FAIL}
    assert recon.status is not ItemStatus.NOT_TESTED
