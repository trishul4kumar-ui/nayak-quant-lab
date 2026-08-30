from __future__ import annotations

from pathlib import Path

import pytest

from quantlab import __version__
from quantlab.core.config import LiveSafetyGates
from quantlab.discovery.experiment import run_named_discovery_search
from quantlab.discovery.search import SearchBudget
from quantlab.models.registry import ExperimentLedger
from quantlab.research.gate import GateOutcome


@pytest.mark.discovery
def test_discovery_e2e_synthetic_cannot_promote(tmp_path: Path) -> None:
    budget = SearchBudget(population_size=6, n_generations=2, max_candidates=12, seed=7)
    report, run = run_named_discovery_search(
        "GP-MOM-VOL-001",
        ledger_path=tmp_path / "ledger.jsonl",
        n_days=80,
        fabric_root=tmp_path / "fabric",
        budget=budget,
        append=True,
    )
    assert report.gate is not None
    assert report.gate.outcome in {GateOutcome.WARN, GateOutcome.REJECT}
    assert report.gate.outcome is not GateOutcome.RESEARCH_CANDIDATE
    assert run.selection_stage == "discovery"
    assert run.search_family_id == "GP-MOM-VOL-001"
    assert run.tested_count == report.tested_count
    assert run.expression_hash
    assert LiveSafetyGates().live_trading is False
    assert __version__ == "3.1.0"
    rows = ExperimentLedger(tmp_path / "ledger.jsonl").list_runs()
    assert any(row.selection_stage == "discovery" for row in rows)
    assert (tmp_path / "artifacts" / run.id / "discovery.json").is_file()
