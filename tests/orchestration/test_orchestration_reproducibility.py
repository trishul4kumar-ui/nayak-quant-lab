from __future__ import annotations

from pathlib import Path

import pytest

from quantlab.orchestration.experiment import run_named_orchestration_experiment


@pytest.mark.orchestration
def test_same_inputs_same_result(tmp_path: Path) -> None:
    kwargs = dict(
        ledger_path=tmp_path / "ledger.jsonl",
        n_days=80,
        fabric_root=tmp_path / "fabric",
        append=False,
    )
    a, _ = run_named_orchestration_experiment("EXP-MOM-001", **kwargs)
    b, _ = run_named_orchestration_experiment("EXP-MOM-001", **kwargs)
    assert a.config_hash == b.config_hash
    assert a.discovery.attempted == b.discovery.attempted
    assert [c.config_hash for c in a.candidates] == [c.config_hash for c in b.candidates]
