from __future__ import annotations

from pathlib import Path

import pytest

from quantlab.discovery.experiment import run_named_discovery_search
from quantlab.discovery.search import SearchBudget
from quantlab.research.gate import GateOutcome


@pytest.mark.discovery
def test_genetic_search_records_every_candidate(tmp_path: Path) -> None:
    budget = SearchBudget(population_size=6, n_generations=2, max_candidates=12, seed=7)
    report, run = run_named_discovery_search(
        "GP-MOM-VOL-001",
        ledger_path=tmp_path / "ledger.jsonl",
        n_days=80,
        fabric_root=tmp_path / "fabric",
        budget=budget,
        append=True,
    )
    assert report.tested_count >= 6
    assert report.tested_count == len(report.candidates)
    assert report.hidden is False
    assert run.selection_stage == "discovery"
    hashes = [item.expression_hash for item in report.candidates]
    assert hashes
    assert report.gate is not None
    assert report.gate.outcome is not GateOutcome.RESEARCH_CANDIDATE
    assert report.live_trading is False
