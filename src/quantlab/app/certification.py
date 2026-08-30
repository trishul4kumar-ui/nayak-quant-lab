"""App-layer certification. Qt cannot force CERTIFIED or live mode."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel

from quantlab.certification.enums import CertificationState, ReviewerRole, SuspensionReason
from quantlab.certification.experiment import run_certification_experiment
from quantlab.certification.models import CertificationRequest, CertificationResult
from quantlab.certification.reporting import result_report
from quantlab.certification.service import (
    certify,
    create_candidate,
    diff_candidates,
    reproduce_candidate,
    retire,
    suspend,
    transition,
)
from quantlab.certification.state import get_result, last_result, list_runs
from quantlab.core.config import get_settings


def _dump(model: BaseModel) -> dict[str, Any]:
    return model.model_dump(mode="json")


def _ledger_path(raw: str) -> Path:
    if raw:
        return Path(raw)
    return Path(get_settings().experiment_ledger_path)


def list_payload() -> list[dict[str, Any]]:
    rows = [
        {
            "candidate_id": item.candidate.candidate_id,
            "state": item.state.value,
            "blocked": item.blocked,
            "live_trading": False,
        }
        for item in list_runs()
    ]
    if not rows:
        rows.append(
            {
                "note": "No certification candidates. quantlab validation create",
                "live_trading": False,
            }
        )
    return rows


def inspect_payload(candidate_id: str) -> dict[str, Any]:
    result = get_result(candidate_id)
    if result is None:
        return {"error": "no certification candidate yet"}
    payload = _dump(result.run)
    payload["state"] = result.state.value
    payload["live_trading"] = False
    payload["note"] = "Inspect. CERTIFIED is not live."
    return payload


def create_payload(*, candidate_id: str = "seed-candidate", ledger: str = "") -> dict[str, Any]:
    result = create_candidate(CertificationRequest(candidate_id=candidate_id))
    _persist(result, ledger)
    return result_report(result)


def run_payload(*, candidate_id: str = "last", ledger: str = "") -> dict[str, Any]:
    result, row = run_certification_experiment(
        CertificationRequest(candidate_id=candidate_id),
        ledger_path=_ledger_path(ledger),
    )
    _persist(result, ledger)
    payload = result_report(result)
    payload["ledger_id"] = row.id
    return payload


def _persist(result: CertificationResult, ledger: str) -> None:
    try:
        from quantlab.knowledge.ingest import persist_certification

        persist_certification(result, _ledger_path(ledger))
    except Exception:
        pass


def _need() -> CertificationResult:
    result = last_result()
    if result is None:
        run_payload()
        result = last_result()
    assert result is not None
    return result


def checklist_payload(candidate_id: str = "last") -> dict[str, Any]:
    result = get_result(candidate_id) or _need()
    return {
        "items": [_dump(item) for item in result.checklist],
        "live_trading": False,
    }


def reproduce_payload(candidate_id: str = "last") -> dict[str, Any]:
    result = reproduce_candidate(candidate_id)
    replay = result.reproduction
    return {"missing": True} if replay is None else _dump(replay)


def risk_payload(candidate_id: str = "last") -> dict[str, Any]:
    result = get_result(candidate_id) or _need()
    return {"risks": [_dump(item) for item in result.risks], "live_trading": False}


def domain_payload(code: str, candidate_id: str = "last") -> dict[str, Any]:
    result = get_result(candidate_id) or _need()
    match = [item for item in result.checklist if item.code.value == code]
    if not match:
        return {"missing": True, "code": code}
    return _dump(match[0])


def certify_payload(candidate_id: str = "last") -> dict[str, Any]:
    result = certify(
        candidate_id,
        request=CertificationRequest(
            candidate_id=candidate_id,
            role=ReviewerRole.CERTIFICATION_REVIEWER,
        ),
    )
    return result_report(result)


def suspend_payload(candidate_id: str = "last") -> dict[str, Any]:
    result = suspend(candidate_id, SuspensionReason.VALIDATION_EXPIRY)
    return result_report(result)


def retire_payload(candidate_id: str = "last") -> dict[str, Any]:
    return result_report(retire(candidate_id))


def report_payload(candidate_id: str = "last") -> dict[str, Any]:
    result = get_result(candidate_id) or _need()
    return result_report(result)


def lineage_payload(candidate_id: str = "last") -> dict[str, Any]:
    result = get_result(candidate_id) or _need()
    return {
        "candidate_id": result.candidate.candidate_id,
        "family_id": result.candidate.family_id,
        "snapshot_id": result.candidate.snapshot_id,
        "software_version": result.candidate.software_version,
        "live_trading": False,
    }


def diff_payload(left_id: str, right_id: str) -> dict[str, Any]:
    return diff_candidates(left_id, right_id)


def advance_payload(candidate_id: str, target: str) -> dict[str, Any]:
    result = transition(candidate_id, CertificationState(target))
    return result_report(result)


def last_run_row() -> dict[str, Any] | None:
    result = last_result()
    if result is None:
        return None
    return {
        "id": result.run.certification_id,
        "candidate": result.candidate.candidate_id,
        "state": result.state.value,
        "blocked": result.blocked,
        "hash": result.run.validation_hash,
    }
