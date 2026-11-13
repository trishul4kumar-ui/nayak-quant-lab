from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from quantlab.app.bootstrap import bootstrap
from quantlab.broker_gateway.mock import MockBrokerAdapter
from quantlab.broker_gateway.service import matching_internal_books
from quantlab.capital.library import seed_covariance
from quantlab.core.errors import DataIntegrityError, SafetyError
from quantlab.data.policy import fixtures_enabled, require_real_data
from quantlab.data.providers.memory import MemoryBarProvider
from quantlab.data.providers.research import ResearchBarProvider
from quantlab.econometrics.library import panel_toy, random_walk, stationary_ar1
from quantlab.econometrics.service import run_econometrics
from quantlab.knowledge.memory import seed_graph
from quantlab.paper_oms.library import seed_account, seed_decision, seed_snapshot, seed_target
from quantlab.realtime_data.mock import MockMarketDataAdapter, seed_observations
from quantlab.realtime_decision.models import synthetic_research_release
from quantlab.release.service import default_passing_request
from quantlab.research.pipeline import load_synthetic_frame


@pytest.fixture
def production(monkeypatch):
    monkeypatch.delenv("_QUANTLAB_TEST_FIXTURES", raising=False)
    assert not fixtures_enabled()


@pytest.mark.parametrize(
    "generate",
    [
        MemoryBarProvider,
        MockMarketDataAdapter,
        MockBrokerAdapter,
        seed_account,
        seed_decision,
        seed_snapshot,
        seed_target,
        seed_covariance,
        seed_observations,
        run_econometrics,
        matching_internal_books,
        default_passing_request,
        lambda: stationary_ar1(n=20, seed=1),
        lambda: random_walk(n=20, seed=1),
        lambda: panel_toy(n_entity=2, n_time=5, seed=1),
        lambda: synthetic_research_release(as_of=datetime.now(UTC)),
    ],
)
def test_production_cannot_generate_fixture_inputs(production, generate):
    with pytest.raises(DataIntegrityError, match="REAL_DATA_REQUIRED"):
        generate()


@pytest.mark.parametrize("kind", ["synthetic", "SYNTHETIC", "", "unknown", "mock"])
def test_production_rejects_nonreal_admission(production, kind):
    with pytest.raises(DataIntegrityError, match="REAL_DATA_REQUIRED"):
        require_real_data(kind, source="historical experiment")


def test_explicit_real_kind_admission(production):
    require_real_data("REAL", source="verified source")


@pytest.mark.parametrize("source", ["mock-readonly", "memory_synthetic_nse", "synthetic", ""])
def test_cannot_relabel_obvious_fixture_source_as_real(production, source):
    with pytest.raises(DataIntegrityError, match="REAL_DATA_REQUIRED"):
        require_real_data("REAL", source=source)


def make_csv_dataset(tmp_path):
    """Transport/source fixture for reader contract tests, not real market evidence."""
    from quantlab.data.fabric.catalog import DatasetCatalog
    from quantlab.data.fabric.ingest import ingest_csv
    from quantlab.data.fabric.layout import FabricLayout

    source = tmp_path / "reader-contract-fixture.csv"
    source.write_text(
        "exchange,symbol,event_time,effective_time,available_time,open,high,low,close,volume\n"
        "BSE,BEL,2024-01-02T10:00:00+00:00,2024-01-02T10:00:00+00:00,"
        "2024-01-02T10:00:00+00:00,100,105,95,102,1000\n"
        "BSE,BEL,2024-01-03T10:00:00+00:00,2024-01-03T10:00:00+00:00,"
        "2024-01-03T10:00:00+00:00,102,106,99,104,1100\n",
        encoding="utf-8",
    )
    layout = FabricLayout(tmp_path / "fabric")
    record = ingest_csv(source, layout, dataset_id="reader-test", version="v1").record
    record = record.model_copy(
        update={
            "extra": {**record.extra, "historical_availability_verified": "true"},
        }
    )
    with DatasetCatalog(layout) as catalog:
        catalog.upsert(record)
    return layout, record


def test_version_pinned_real_reader_uses_exact_source(tmp_path, monkeypatch):
    from quantlab.core.config import get_settings

    layout, record = make_csv_dataset(tmp_path)
    monkeypatch.delenv("_QUANTLAB_TEST_FIXTURES", raising=False)
    monkeypatch.setenv("QUANT_LAB_RESEARCH_DATASET", "reader-test@v1")
    monkeypatch.setenv("QUANT_LAB_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    frame = load_synthetic_frame(fabric_root=layout.root)
    assert frame.record.checksum == record.checksum
    assert len(frame.flat) == 2
    assert all(bar.data_kind == "real" for bar in frame.flat)
    assert frame.flat[-1].close == 104
    assert len(ResearchBarProvider().all_bars()) == 1
    assert len(load_synthetic_frame(fabric_root=layout.root, n_days=1).flat) == 1


@pytest.mark.parametrize("fault", ["kind", "state", "vintage", "checksum", "bar", "version"])
def test_real_reader_rejects_unverified_or_tampered_inputs(tmp_path, monkeypatch, fault):
    from quantlab.core.config import get_settings
    from quantlab.data.fabric.catalog import DatasetCatalog
    from quantlab.data.fabric.store import PitStore
    from quantlab.data.fabric.types import DataKind, DatasetState

    layout, record = make_csv_dataset(tmp_path)
    if fault == "kind":
        record = record.model_copy(update={"data_kind": DataKind.SYNTHETIC})
    elif fault == "state":
        record = record.model_copy(update={"state": DatasetState.NOT_READY})
    elif fault == "vintage":
        record = record.model_copy(
            update={
                "extra": {
                    **record.extra,
                    "historical_availability_verified": "false",
                }
            }
        )
    elif fault == "checksum":
        record = record.model_copy(update={"checksum": "0" * 64})
    else:
        store = PitStore(layout, "reader-test", "v1")
        bars = store.query(as_of=datetime(2025, 1, 1, tzinfo=UTC))
        changes = {"close": 103.0} if fault == "bar" else {"dataset_version": "other"}
        store.write_bars([bars[0].model_copy(update=changes), bars[1]])
    with DatasetCatalog(layout) as catalog:
        catalog.upsert(record)
    monkeypatch.delenv("_QUANTLAB_TEST_FIXTURES", raising=False)
    monkeypatch.setenv("QUANT_LAB_RESEARCH_DATASET", "reader-test@v1")
    get_settings.cache_clear()
    with pytest.raises(DataIntegrityError):
        load_synthetic_frame(fabric_root=layout.root)


def test_no_automatic_seed_or_implicit_latest_dataset(production, tmp_path: Path, monkeypatch):
    from quantlab.core.config import get_settings

    monkeypatch.setenv("QUANT_LAB_RESEARCH_DATASET", "")
    get_settings.cache_clear()
    with pytest.raises(DataIntegrityError, match="REAL_VALIDATED_DATASET_REQUIRED"):
        load_synthetic_frame(fabric_root=tmp_path / "fabric")
    assert not list(tmp_path.rglob("*.parquet"))
    with pytest.raises(DataIntegrityError, match="REAL_VALIDATED_DATASET_REQUIRED"):
        ResearchBarProvider()
    assert not seed_graph().nodes


def test_legacy_job_cannot_silently_change_strategy_or_generate(production, tmp_path, monkeypatch):
    monkeypatch.setenv("QUANT_LAB_RESEARCH_DATASET", "")
    runtime = bootstrap(data_dir=tmp_path)
    try:
        with pytest.raises(SafetyError, match="REAL_VALIDATED_DATASET_REQUIRED"):
            runtime.submit_momentum_backtest()
        with pytest.raises(SafetyError, match="REAL_VALIDATION_INPUTS_REQUIRED"):
            runtime.submit_momentum_validation()
        assert not runtime.jobs.list_jobs()
        assert not runtime.ledger.list_runs()
        assert not runtime.gates.live_trading
        assert not runtime.gates.broker_write_enabled
    finally:
        runtime.shutdown()


def test_defaults_select_real_adapters_without_mock_fallback(production, monkeypatch):
    from quantlab.broker_gateway import service as broker
    from quantlab.broker_gateway.kite import KiteReadOnlyAdapter
    from quantlab.realtime_data import service as market
    from quantlab.realtime_data.kite import KiteMarketDataAdapter

    market.reset_for_tests()
    broker.reset_for_tests()
    sentinel = object()
    monkeypatch.setattr(KiteMarketDataAdapter, "from_environment", lambda: sentinel)
    monkeypatch.setattr(KiteReadOnlyAdapter, "from_environment", lambda: sentinel)
    try:
        assert market.health().active_source == "kite-rest-quote-v3"
        assert market._adapter() is sentinel
        assert broker._adapter() is sentinel
    finally:
        market.reset_for_tests()
        broker.reset_for_tests()


def test_default_quote_capture_connects_same_real_adapter_and_rejects_empty(
    production, monkeypatch
):
    from quantlab.realtime_data import service
    from quantlab.realtime_data.errors import RealTimeDataError
    from quantlab.realtime_data.kite import KiteMarketDataAdapter
    from quantlab.realtime_data.production import ProductionFeedSource, ProductionMarketDataAdapter

    class EmptySource(ProductionMarketDataAdapter):
        def __init__(self):
            super().__init__((ProductionFeedSource(source_id="test-observed-source", priority=1),))
            self.connections = 0

        def connect(self):
            self.connections += 1
            return super().connect()

    service.reset_for_tests()
    adapter = EmptySource()
    monkeypatch.setattr(KiteMarketDataAdapter, "from_environment", lambda: adapter)
    try:
        with pytest.raises(RealTimeDataError, match="no observations"):
            service.snapshot()
        assert adapter.connections == 1
        assert service._adapter() is adapter
        assert not service.list_snapshots()
    finally:
        service.reset_for_tests()
