from __future__ import annotations

from pathlib import Path

import pytest

from quantlab.discovery.experiment import planted_label, run_named_discovery_search
from quantlab.discovery.registry import get_family
from quantlab.discovery.search import SearchBudget
from quantlab.features.engine import compute_panel, session_calendar
from quantlab.features.registry import get_feature
from quantlab.research.pipeline import load_synthetic_frame


@pytest.mark.discovery
def test_known_alpha_recovery_uses_planted_features(tmp_path: Path) -> None:
    family = get_family("GP-MOM-VOL-001")
    frame = load_synthetic_frame(
        n_days=80,
        ledger_path=tmp_path / "ledger.jsonl",
        fabric_root=tmp_path / "fabric",
    )
    dates = session_calendar(frame.bars)
    panels = {
        fid: compute_panel(get_feature(fid), frame.bars, as_of_times=dates)
        for fid in family.grammar.allowed_features
    }
    budget = SearchBudget(population_size=6, n_generations=2, max_candidates=12, seed=7)
    report, _run = run_named_discovery_search(
        "GP-MOM-VOL-001",
        ledger_path=tmp_path / "ledger.jsonl",
        n_days=80,
        fabric_root=tmp_path / "fabric",
        budget=budget,
        label_panel=planted_label(panels),
        append=True,
    )
    text = report.elite_text
    assert any(token in text for token in ("momentum_5", "rolling_std_20", "momentum_20"))
    assert report.train_ic is not None
