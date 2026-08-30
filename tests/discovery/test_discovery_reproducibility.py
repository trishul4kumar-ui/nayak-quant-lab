from __future__ import annotations

from pathlib import Path

import pytest

from quantlab.discovery.experiment import run_named_discovery_search
from quantlab.discovery.search import SearchBudget


@pytest.mark.discovery
def test_same_seed_replays_elite(tmp_path: Path) -> None:
    budget = SearchBudget(population_size=6, n_generations=2, max_candidates=10, seed=13)
    kwargs = dict(
        family_id="GP-MOM-VOL-001",
        n_days=80,
        fabric_root=tmp_path / "fabric",
        budget=budget,
        append=True,
    )
    report_a, _ = run_named_discovery_search(ledger_path=tmp_path / "a.jsonl", **kwargs)
    report_b, _ = run_named_discovery_search(ledger_path=tmp_path / "b.jsonl", **kwargs)
    assert report_a.elite_hash == report_b.elite_hash
    assert report_a.tested_count == report_b.tested_count
