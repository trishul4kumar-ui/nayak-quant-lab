"""Factor research uses the Prompt 05 gate. Synthetic cannot promote."""

from __future__ import annotations

from pathlib import Path

import pytest

from quantlab.data.providers.memory import MemoryBarProvider
from quantlab.domain.models import Instrument
from quantlab.domain.research import CheckResult
from quantlab.factors.experiment import (
    factor_pair_correlation,
    run_factor_experiment,
    run_named_factor_experiment,
)
from quantlab.factors.registry import get_factor
from quantlab.research.gate import GateOutcome


@pytest.mark.factor
def test_synthetic_factor_cannot_promote(tmp_path: Path) -> None:
    report, run, panel = run_named_factor_experiment(
        "style_momentum_20",
        ledger_path=tmp_path / "ledger.jsonl",
        n_days=80,
        fabric_root=tmp_path / "fabric",
        append=True,
    )
    assert report.gate.outcome is GateOutcome.WARN
    assert report.gate.outcome is not GateOutcome.RESEARCH_CANDIDATE
    assert report.data_kind == "synthetic"
    assert report.integrity["synthetic_data"] == "warn"
    assert report.integrity["future_factor"] == "pass"
    assert panel
    assert run.factor_id == "style_momentum_20"
    assert (tmp_path / "ledger.jsonl").exists()
    assert (tmp_path / "artifacts" / run.id / "ic.json").is_file()


@pytest.mark.factor
def test_leaky_factor_fails_integrity() -> None:
    provider = MemoryBarProvider(n_days=80)
    bars = provider.all_bars()
    instruments = [Instrument(id=inst, name=inst.symbol) for inst in bars]
    report, run, _ = run_factor_experiment(
        bars=bars,
        instruments=instruments,
        definition=get_factor("style_momentum_20"),
        data_kind="synthetic",
        leaked_label=True,
        append=False,
    )
    assert report.integrity["future_factor"] == "fail"
    assert report.integrity["label_as_feature"] == "fail"
    assert report.gate.outcome is GateOutcome.REJECT
    assert run.status.value == "failed"


@pytest.mark.factor
def test_not_implemented_factor_stays_not_tested() -> None:
    provider = MemoryBarProvider(n_days=40)
    bars = provider.all_bars()
    instruments = [Instrument(id=inst, name=inst.symbol) for inst in bars]
    report, _, panel = run_factor_experiment(
        bars=bars,
        instruments=instruments,
        definition=get_factor("liquidity_adv"),
        data_kind="synthetic",
        append=False,
    )
    assert panel == {}
    assert report.observation.status is CheckResult.NOT_TESTED
    assert report.gate.outcome is GateOutcome.WARN


@pytest.mark.factor
def test_factor_correlation_is_defined() -> None:
    bars = MemoryBarProvider(n_days=80).all_bars()
    pair = factor_pair_correlation("style_momentum_20", "style_volatility_20", bars)
    assert pair.n > 0
    assert pair.feature_a == "style_momentum_20"
