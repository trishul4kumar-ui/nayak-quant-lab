"""Live-certification ledger rows. Reuses JSONL ExperimentLedger."""

from __future__ import annotations

from contextlib import suppress
from pathlib import Path

from quantlab import __version__
from quantlab.domain.models import ExperimentRun, ExperimentStatus
from quantlab.knowledge.errors import KnowledgeError
from quantlab.models.registry import ExperimentLedger
from quantlab.release.models import CertificationRequest, CertificationResult
from quantlab.release.repository import put
from quantlab.release.service import evaluate
from quantlab.research.envinfo import environment, git_commit, git_dirty


def _run_row(result: CertificationResult) -> ExperimentRun:
    pkg = result.package
    manifest = result.manifest
    return ExperimentRun(
        id=result.evaluation_id,
        name=f"live-cert:{result.state.value}",
        hypothesis="Live-trading certification is not live enablement.",
        status=(
            ExperimentStatus.PASSED
            if result.state.value == "certified"
            else ExperimentStatus.FAILED
        ),
        git_commit=git_commit(),
        dataset_version="live-certification",
        universe=[],
        feature_versions={},
        label_definition="not_applicable",
        hyperparameters={"seed": 0},
        transaction_cost_bps=10.0,
        snapshot_id=pkg.package_hash if pkg else "",
        data_kind=pkg.data_kind if pkg else "synthetic",
        application_version=__version__,
        python_version=environment().get("python", ""),
        git_dirty=git_dirty(),
        selection_stage="certification",
        live_certification_id=result.evaluation_id,
        live_certification_hash=result.result_hash,
        release_id=manifest.release_id if manifest else "",
        release_manifest_hash=manifest.manifest_hash if manifest else "",
        approval_id=manifest.approved_by if manifest else "",
        release_blocked=True,
    )


def persist_release(result: CertificationResult, ledger_path: Path) -> None:
    from quantlab.knowledge.ingest import persist_release as ingest_persist

    with suppress(KnowledgeError, OSError):
        ingest_persist(result, ledger_path)


def run_release_experiment(
    request: CertificationRequest | None = None,
    *,
    ledger_path: Path | None = None,
) -> tuple[CertificationResult, ExperimentRun]:
    result = evaluate(request)
    put(result)
    row = _run_row(result)
    path = ledger_path or Path("experiments/ledger.jsonl")
    ExperimentLedger(path).append(row)
    persist_release(result, path)
    return result, row
