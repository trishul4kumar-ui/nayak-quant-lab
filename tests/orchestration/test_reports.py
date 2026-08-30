from __future__ import annotations

from pathlib import Path

import pytest

from quantlab.orchestration.experiment import run_named_orchestration_experiment


@pytest.mark.orchestration
def test_report_answers_the_scientific_question(tmp_path: Path) -> None:
    report, _ = run_named_orchestration_experiment(
        "EXP-MOM-001",
        ledger_path=tmp_path / "ledger.jsonl",
        n_days=80,
        fabric_root=tmp_path / "fabric",
        append=False,
    )
    narrative = report.as_narrative()
    assert "candidates" in narrative
    assert "gate=" in narrative
    assert "Synthetic cannot promote" in narrative
    assert report.discovery.attempted >= 4
    assert report.not_tested is not None
    assert "FACT" in report.note
    assert "NOT_TESTED" in report.note
