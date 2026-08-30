"""App-facing certification report."""

from __future__ import annotations

from typing import Any

from quantlab.certification.models import CertificationResult


def result_report(result: CertificationResult) -> dict[str, Any]:
    return {
        "certification_id": result.run.certification_id,
        "candidate_id": result.candidate.candidate_id,
        "state": result.state.value,
        "blocked": result.blocked,
        "block_reasons": result.block_reasons,
        "checklist_hash": result.run.checklist_hash,
        "validation_hash": result.run.validation_hash,
        "open_findings": [
            item.code.value for item in result.checklist if item.status.value != "pass"
        ],
        "waivers": [item.waiver_id for item in result.waivers],
        "live_trading": False,
        "note": result.note,
    }
