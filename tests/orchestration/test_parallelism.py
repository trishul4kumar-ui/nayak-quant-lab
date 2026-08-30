from __future__ import annotations

from pathlib import Path

import pytest

from quantlab.orchestration.experiment import run_orchestration_experiment
from quantlab.orchestration.registry import get_spec


@pytest.mark.orchestration
def test_parallel_order_does_not_change_results(tmp_path: Path) -> None:
    spec = get_spec("EXP-MOM-001")
    first, _ = run_orchestration_experiment(
        spec,
        ledger_path=tmp_path / "a.jsonl",
        fabric_root=tmp_path / "fa",
        append=False,
        execution_order=None,
        include_execution=False,
    )
    n = first.discovery.attempted
    second, _ = run_orchestration_experiment(
        spec,
        ledger_path=tmp_path / "b.jsonl",
        fabric_root=tmp_path / "fb",
        append=False,
        include_execution=False,
        execution_order=list(range(n - 1, -1, -1)),
    )
    by_id = {c.candidate_id: c.total_return for c in first.candidates}
    for item in second.candidates:
        assert item.total_return == by_id[item.candidate_id]
