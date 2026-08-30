"""Canonical hashes for certification objects."""

from __future__ import annotations

from typing import Any

from quantlab.backtest.spec import config_hash
from quantlab.certification.models import Candidate, CertificationRun, ChecklistItem


def _dump(payload: dict[str, Any]) -> str:
    return config_hash(payload)


def hash_candidate(candidate: Candidate) -> str:
    return _dump(candidate.model_dump(mode="json", exclude={"note"}))


def hash_checklist(items: list[ChecklistItem]) -> str:
    return _dump({"items": [item.model_dump(mode="json", exclude={"note"}) for item in items]})


def hash_validation(candidate: Candidate, items: list[ChecklistItem]) -> str:
    return _dump(
        {
            "candidate": hash_candidate(candidate),
            "checklist": hash_checklist(items),
        }
    )


def hash_run(run: CertificationRun) -> str:
    return _dump(run.model_dump(mode="json", exclude={"validation_hash", "note"}))


def idempotency_key(*, candidate_id: str, software_version: str, snapshot_id: str) -> str:
    return _dump(
        {
            "candidate_id": candidate_id,
            "software_version": software_version,
            "snapshot_id": snapshot_id,
        }
    )
