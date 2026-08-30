from __future__ import annotations

from pathlib import Path

import pytest

from quantlab.discovery.experiment import random_label, run_named_discovery_search
from quantlab.discovery.search import SearchBudget
from quantlab.features.engine import compute_panel, session_calendar
from quantlab.features.registry import get_feature
from quantlab.research.gate import GateOutcome
from quantlab.research.pipeline import load_synthetic_frame


@pytest.mark.discovery
def test_null_search_does_not_promote(tmp_path: Path) -> None:
    frame = load_synthetic_frame(
        n_days=80,
        ledger_path=tmp_path / "ledger.jsonl",
        fabric_root=tmp_path / "fabric",
    )
    dates = session_calendar(frame.bars)
    template = compute_panel(get_feature("momentum_20"), frame.bars, as_of_times=dates)
    budget = SearchBudget(population_size=6, n_generations=2, max_candidates=10, seed=21)
    report, run = run_named_discovery_search(
        "GP-MOM-VOL-001",
        ledger_path=tmp_path / "ledger.jsonl",
        n_days=80,
        fabric_root=tmp_path / "fabric",
        budget=budget,
        label_panel=random_label(template, seed=99),
        append=True,
    )
    assert report.gate is not None
    assert report.gate.outcome is not GateOutcome.RESEARCH_CANDIDATE
    assert run.data_kind == "synthetic"
    if report.multiple_testing is not None:
        assert report.multiple_testing.n_hypotheses >= 1
