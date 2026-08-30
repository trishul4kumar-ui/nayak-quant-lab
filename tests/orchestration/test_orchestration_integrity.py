from __future__ import annotations

from pathlib import Path

import pytest

from quantlab.orchestration.experiment import run_orchestration_experiment
from quantlab.orchestration.leaks import OrchestrationLeakFlags
from quantlab.orchestration.registry import get_spec
from quantlab.research.gate import GateOutcome


@pytest.mark.orchestration
def test_parameter_change_after_freeze_fails(tmp_path: Path) -> None:
    frozen = get_spec("EXP-MOM-001")
    mutated = frozen.model_copy(update={"lookback": 5})
    report, _ = run_orchestration_experiment(
        mutated,
        frozen=frozen,
        ledger_path=tmp_path / "ledger.jsonl",
        fabric_root=tmp_path / "fabric",
        append=False,
        include_execution=False,
    )
    assert report.pit_integrity["experiment_identity_mutation"] == "fail"
    assert report.pit_integrity["experiment_config_mutation"] == "fail"


@pytest.mark.orchestration
def test_hidden_candidate_fails(tmp_path: Path) -> None:
    spec = get_spec("EXP-MOM-001")
    report, _ = run_orchestration_experiment(
        spec,
        ledger_path=tmp_path / "ledger.jsonl",
        fabric_root=tmp_path / "fabric",
        append=False,
        include_execution=False,
        leaks=OrchestrationLeakFlags(hidden_candidate=True),
    )
    assert report.pit_integrity["hidden_candidate"] == "fail"
    assert report.gate.outcome is GateOutcome.REJECT


@pytest.mark.orchestration
def test_posthoc_stopping_fails(tmp_path: Path) -> None:
    spec = get_spec("EXP-MOM-001")
    report, _ = run_orchestration_experiment(
        spec,
        ledger_path=tmp_path / "ledger.jsonl",
        fabric_root=tmp_path / "fabric",
        append=False,
        include_execution=False,
        leaks=OrchestrationLeakFlags(posthoc_stopping=True),
    )
    assert report.pit_integrity["posthoc_stopping"] == "fail"


@pytest.mark.orchestration
def test_snapshot_mismatch_fails(tmp_path: Path) -> None:
    spec = get_spec("EXP-MOM-001").model_copy(update={"snapshot_id": "not-this-snapshot"})
    frozen = spec
    report, _ = run_orchestration_experiment(
        spec,
        frozen=frozen,
        ledger_path=tmp_path / "ledger.jsonl",
        fabric_root=tmp_path / "fabric",
        append=False,
        include_execution=False,
    )
    assert report.pit_integrity["dataset_snapshot_mismatch"] == "fail"


@pytest.mark.orchestration
def test_result_overwrite_and_family_undercount(tmp_path: Path) -> None:
    spec = get_spec("EXP-MOM-001")
    report, _ = run_orchestration_experiment(
        spec,
        ledger_path=tmp_path / "ledger.jsonl",
        fabric_root=tmp_path / "fabric",
        append=False,
        include_execution=False,
        leaks=OrchestrationLeakFlags(
            result_overwrite=True,
            hidden_failed_experiment=True,
            holdout_reuse=True,
            future_cost_selection=True,
        ),
        hide_failures=True,
    )
    assert report.pit_integrity["result_overwrite"] == "fail"
    assert report.pit_integrity["holdout_reuse"] == "fail"
    assert report.pit_integrity["future_cost_selection"] == "fail"
