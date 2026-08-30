from __future__ import annotations

from pathlib import Path

import pytest

from quantlab import __version__
from quantlab.core.config import LiveSafetyGates
from quantlab.models.registry import ExperimentLedger
from quantlab.orchestration.experiment import run_named_orchestration_experiment
from quantlab.research.gate import GateOutcome


@pytest.mark.orchestration
def test_synthetic_family_cannot_promote(tmp_path: Path) -> None:
    report, run = run_named_orchestration_experiment(
        "EXP-MOM-001",
        ledger_path=tmp_path / "ledger.jsonl",
        n_days=80,
        fabric_root=tmp_path / "fabric",
        append=True,
    )
    assert report.gate.outcome is GateOutcome.WARN or report.gate.outcome is GateOutcome.REJECT
    assert report.gate.outcome is not GateOutcome.RESEARCH_CANDIDATE
    assert report.data_kind == "synthetic"
    assert run.selection_stage == "orchestration"
    assert run.orchestration_id == "EXP-MOM-001"
    assert run.hypothesis_id == "H-MOM-001"
    assert run.research_family_id == "MOM-FAMILY-001"
    assert run.candidate_count >= 4
    assert run.tested_count == run.candidate_count
    assert LiveSafetyGates().live_trading is False
    assert __version__ == "3.1.0"
    ledger = ExperimentLedger(tmp_path / "ledger.jsonl")
    rows = ledger.list_runs()
    assert len(rows) == report.discovery.attempted + 1
    assert all(row.selection_stage == "orchestration" for row in rows)
    assert (tmp_path / "artifacts" / run.id / "orchestration.json").is_file()
    assert "cs_momentum_inverted" in {c.strategy_id for c in report.candidates}
    assert "equal_weight" in {c.strategy_id for c in report.candidates}
    assert report.multiple_testing.n_hypotheses >= 1
    assert report.execution_cost is not None
    assert report.lineage.nodes
