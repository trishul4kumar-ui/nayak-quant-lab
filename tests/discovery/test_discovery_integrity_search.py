from __future__ import annotations

from pathlib import Path

import pytest

from quantlab.discovery.experiment import run_named_discovery_search
from quantlab.discovery.integrity import DiscoveryLeakFlags
from quantlab.discovery.search import SearchBudget
from quantlab.domain.research import CheckResult
from quantlab.research.gate import GateOutcome


@pytest.mark.discovery
def test_hidden_candidate_fails_integrity(tmp_path: Path) -> None:
    budget = SearchBudget(population_size=6, n_generations=2, max_candidates=10, seed=7)
    report, _run = run_named_discovery_search(
        "GP-MOM-VOL-001",
        ledger_path=tmp_path / "ledger.jsonl",
        n_days=80,
        fabric_root=tmp_path / "fabric",
        budget=budget,
        leaks=DiscoveryLeakFlags(hidden_candidate=True, posthoc_search_budget=True),
        append=True,
    )
    assert report.pit_integrity.get("hidden_candidate") == CheckResult.FAIL.value
    assert report.pit_integrity.get("posthoc_search_budget") == CheckResult.FAIL.value
    assert report.gate is not None
    assert report.gate.outcome is GateOutcome.REJECT
