from __future__ import annotations

from pathlib import Path

import pytest

from quantlab.orchestration.ablation import ablating_lookback
from quantlab.orchestration.experiment import run_named_orchestration_experiment


@pytest.mark.orchestration
def test_ablation_records_lookback_delta(tmp_path: Path) -> None:
    report, _run = run_named_orchestration_experiment(
        "EXP-MOM-001",
        ledger_path=tmp_path / "ledger.jsonl",
        n_days=80,
        fabric_root=tmp_path / "fabric",
        append=False,
    )
    ablation = ablating_lookback(report.candidates, cost_bps=10.0)
    assert ablation.rows
    row = ablation.rows[0]
    assert row.with_component is not None
    assert row.without_component is not None
