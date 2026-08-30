from __future__ import annotations

from pathlib import Path

import pytest

from quantlab.orchestration.experiment import run_named_orchestration_experiment
from quantlab.orchestration.sensitivity import cost_sensitivity


@pytest.mark.orchestration
def test_cost_sensitivity_uses_recorded_cells(tmp_path: Path) -> None:
    report, _run = run_named_orchestration_experiment(
        "EXP-MOM-001",
        ledger_path=tmp_path / "ledger.jsonl",
        n_days=80,
        fabric_root=tmp_path / "fabric",
        append=False,
    )
    sens = cost_sensitivity(report.candidates, lookback=20)
    assert sens.rows
    assert sens.rows[0].metric_left is not None
    assert sens.rows[0].metric_right is not None
