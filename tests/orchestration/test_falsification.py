from __future__ import annotations

from pathlib import Path

import pytest

from quantlab.orchestration.experiment import run_named_orchestration_experiment
from quantlab.orchestration.falsification import InvertedMomentum


@pytest.mark.orchestration
def test_falsification_is_recorded(tmp_path: Path) -> None:
    report, _run = run_named_orchestration_experiment(
        "EXP-MOM-001",
        ledger_path=tmp_path / "ledger.jsonl",
        n_days=80,
        fabric_root=tmp_path / "fabric",
        append=False,
    )
    inverted = [c for c in report.candidates if c.strategy_id == "cs_momentum_inverted"]
    assert inverted
    assert report.falsification.method
    assert InvertedMomentum().name == "cs_momentum_inverted"
