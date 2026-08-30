from __future__ import annotations

from pathlib import Path

import pytest

from quantlab.orchestration.errors import OrchestrationError
from quantlab.orchestration.registry import get_spec
from quantlab.orchestration.replication import replication_identity
from quantlab.orchestration.snapshot import DatasetSnapshot


@pytest.mark.orchestration
def test_same_snapshot_replication_identity() -> None:
    spec = get_spec("EXP-MOM-001")
    snap = DatasetSnapshot(
        dataset_id="synthetic_nse",
        dataset_version="1",
        snapshot_id="s",
        checksum="c",
    )
    report = replication_identity(spec, spec, snap, snap)
    assert report.same_identity
    assert report.same_snapshot


@pytest.mark.orchestration
def test_snapshot_change_is_contamination() -> None:
    spec = get_spec("EXP-MOM-001")
    a = DatasetSnapshot(
        dataset_id="synthetic_nse",
        dataset_version="1",
        snapshot_id="s1",
        checksum="c1",
    )
    b = a.model_copy(update={"snapshot_id": "s2"})
    with pytest.raises(OrchestrationError, match="contamination"):
        replication_identity(spec, spec, a, b)


@pytest.mark.orchestration
def test_repeat_run_matches_identity(tmp_path: Path) -> None:
    from quantlab.orchestration.experiment import run_named_orchestration_experiment

    first, _ = run_named_orchestration_experiment(
        "EXP-MOM-001",
        ledger_path=tmp_path / "a.jsonl",
        n_days=80,
        fabric_root=tmp_path / "fa",
        append=False,
    )
    second, _ = run_named_orchestration_experiment(
        "EXP-MOM-001",
        ledger_path=tmp_path / "b.jsonl",
        n_days=80,
        fabric_root=tmp_path / "fb",
        append=False,
    )
    assert first.identity_hash == second.identity_hash
    selected = {c.candidate_id: c.total_return for c in first.candidates}
    for item in second.candidates:
        assert item.total_return == selected[item.candidate_id]
