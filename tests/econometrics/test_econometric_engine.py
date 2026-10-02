from __future__ import annotations

from pathlib import Path

import pytest

from quantlab import __version__
from quantlab.core.config import LiveSafetyGates
from quantlab.core.errors import SafetyError
from quantlab.domain.models import ExperimentRun
from quantlab.econometrics.enums import CausalClaim, EstimatorKind
from quantlab.econometrics.identity import hash_spec
from quantlab.econometrics.library import cointegrated_pair, random_walk, stationary_ar1
from quantlab.econometrics.models import EconometricRequest, EconometricSpecification
from quantlab.econometrics.service import run_econometrics
from quantlab.econometrics.var import select_lags
from quantlab.knowledge.entities import NodeType
from quantlab.knowledge.graph import KnowledgeGraph
from quantlab.knowledge.ingest import ingest_econometrics


def test_version() -> None:
    assert __version__ == "3.1.0"


def test_live_trading_gate_remains_false() -> None:
    assert LiveSafetyGates().live_trading is False
    result = run_econometrics()
    assert result.live_trading is False
    assert result.run.live_trading is False


def test_live_request_raises() -> None:
    with pytest.raises(SafetyError):
        run_econometrics(EconometricRequest(live_trading=True))


def test_seed_run_is_synthetic_not_a_claim() -> None:
    result = run_econometrics()
    assert "Synthetic" in result.note or "synthetic" in result.note.lower()
    assert "claim" in result.note.lower() or "CAUSATION" in result.note
    cause = result.diagnostics.causality
    assert cause is not None
    assert cause.claim is CausalClaim.PREDICTIVE


def test_idempotent_same_request() -> None:
    first = run_econometrics(EconometricRequest(seed=3, n=120))
    second = run_econometrics(EconometricRequest(seed=3, n=120))
    assert first.run.econometrics_run_id == second.run.econometrics_run_id
    assert first.run.run_hash == second.run.run_hash


def test_future_payload_ignored_does_not_change_hash() -> None:
    a = run_econometrics(EconometricRequest(seed=4, future_payload_ignored={}))
    b = run_econometrics(EconometricRequest(seed=4, future_payload_ignored={"leak": "ignored"}))
    assert a.run.run_hash == b.run.run_hash


def test_different_seed_different_identity() -> None:
    a = run_econometrics(EconometricRequest(seed=1, spec_id="a"))
    b = run_econometrics(EconometricRequest(seed=2, spec_id="b"))
    assert a.run.econometrics_run_id != b.run.econometrics_run_id


def test_lag_selection_uses_train_window_only() -> None:
    head_y, head_x = cointegrated_pair(n=80, seed=9)
    tail_y = random_walk(n=40, seed=11)
    tail_x = random_walk(n=40, seed=12)
    short = select_lags([head_y, head_x], max_lag=3, train_end=80)
    long = select_lags([head_y + tail_y, head_x + tail_x], max_lag=3, train_end=80)
    assert short == long
    result = run_econometrics()
    assert result.var is not None
    assert result.var.selected_on == "train_window"


def test_full_sample_lag_may_differ_from_train_window() -> None:
    y = stationary_ar1(n=60, seed=1) + random_walk(n=60, seed=2)
    x = stationary_ar1(n=60, seed=3) + random_walk(n=60, seed=4)
    train = select_lags([y, x], max_lag=4, train_end=60)
    full = select_lags([y, x], max_lag=4, train_end=120)
    assert isinstance(train, int)
    assert isinstance(full, int)
    assert 1 <= train <= 4
    assert 1 <= full <= 4


def test_spec_hash_changes_with_formula() -> None:
    from datetime import UTC, datetime

    as_of = datetime(2024, 1, 15, tzinfo=UTC)
    left = EconometricSpecification(
        spec_id="s1",
        estimator=EstimatorKind.OLS,
        series_ids=("y", "x"),
        lags=1,
        as_of=as_of,
    )
    right = EconometricSpecification(
        spec_id="s1",
        estimator=EstimatorKind.HAC,
        series_ids=("y", "x"),
        lags=1,
        as_of=as_of,
    )
    assert hash_spec(left) != hash_spec(right)


def test_family_accounting_reused() -> None:
    result = run_econometrics()
    assert "family_id" in result.multiple_testing
    assert result.run.tested_count >= 0


def test_knowledge_ingest_does_not_require_missing_nodes() -> None:
    result = run_econometrics()
    graph = KnowledgeGraph(graph_id="kg-econo")
    ingest_econometrics(graph, result)
    types = {node.node_type for node in graph.nodes}
    assert NodeType.ECONOMETRIC_RUN in types
    assert NodeType.STATIONARITY_TEST in types
    assert NodeType.CAUSAL_HYPOTHESIS in types


def test_ledger_optional_fields(tmp_path: Path) -> None:
    from quantlab.econometrics.experiment import run_econometrics_experiment

    result, row = run_econometrics_experiment(ledger_path=tmp_path / "ledger.json")
    assert isinstance(row, ExperimentRun)
    assert row.econometrics_run_id == result.run.econometrics_run_id
    assert row.econometrics_hash == result.run.run_hash
    assert row.application_version == "3.1.0"


def test_no_broker_imports() -> None:
    root = Path(__file__).resolve().parents[2] / "src" / "quantlab" / "econometrics"
    forbidden = ("kiteconnect", "zerodha", "openalgo", "quantlab.brokers")
    for path in root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in text, f"{token} in {path}"


@pytest.mark.parametrize("kind", list(EstimatorKind))
def test_estimator_kind_values_are_explicit(kind: EstimatorKind) -> None:
    assert kind.value
    assert kind.value != "live"


def test_johansen_is_not_tested() -> None:
    from quantlab.domain.research import CheckResult
    from quantlab.econometrics.cointegration import johansen_interface

    y, x = cointegrated_pair(n=80, seed=0)
    item = johansen_interface([y, x])
    assert item.status is CheckResult.NOT_TESTED
    assert item.statistic is None


@pytest.mark.parametrize("seed", range(12))
def test_seed_run_completes(seed: int) -> None:
    result = run_econometrics(EconometricRequest(seed=seed, spec_id=f"seed-{seed}"))
    assert result.live_trading is False
    assert result.diagnostics.stationarity


@pytest.mark.parametrize("n", [5, 10, 19])
def test_small_n_stationarity_not_tested(n: int) -> None:
    from quantlab.domain.research import CheckResult
    from quantlab.econometrics.stationarity import adf_test, kpss_test

    series = stationary_ar1(n=n, seed=0)
    assert adf_test(series).status is CheckResult.NOT_TESTED
    assert kpss_test(series).status is CheckResult.NOT_TESTED
