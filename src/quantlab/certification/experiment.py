"""Certification ledger rows."""

from __future__ import annotations

from pathlib import Path

from quantlab import __version__
from quantlab.certification.models import CertificationRequest, CertificationResult
from quantlab.certification.repository import persist
from quantlab.certification.service import run_certification
from quantlab.domain.models import ExperimentRun, ExperimentStatus
from quantlab.models.registry import ExperimentLedger
from quantlab.research.envinfo import environment, git_commit, git_dirty


def _run_row(result: CertificationResult) -> ExperimentRun:
    return ExperimentRun(
        id=result.run.certification_id,
        name=f"certification:{result.state.value}",
        hypothesis="Certification is governance, not live order authority.",
        status=ExperimentStatus.PASSED,
        git_commit=git_commit(),
        dataset_version=result.candidate.snapshot_id,
        universe=[],
        feature_versions=dict(result.candidate.feature_versions),
        label_definition="not_applicable",
        transaction_cost_bps=10.0,
        snapshot_id=result.candidate.snapshot_id,
        data_kind=result.candidate.data_kind,
        metrics={"blocked": 1.0 if result.blocked else 0.0},
        application_version=__version__,
        conclusion="certification observation; not live",
        config_hash=result.run.validation_hash,
        selection_stage="certification",
        git_dirty=git_dirty(),
        python_version=environment().get("python", ""),
        research_type="certification",
        certification_id=result.run.certification_id,
        candidate_id=result.candidate.candidate_id,
        checklist_hash=result.run.checklist_hash,
        validation_hash=result.run.validation_hash,
        certification_state=result.state.value,
        model_risk_severity=max(
            (item.severity.value for item in result.risks),
            default="",
        ),
    )


def run_certification_experiment(
    request: CertificationRequest | None = None,
    *,
    ledger_path: Path,
    append: bool = True,
) -> tuple[CertificationResult, ExperimentRun]:
    result = run_certification(request)
    persist()
    row = _run_row(result)
    if append:
        ExperimentLedger(ledger_path).append(row)
    return result, row
