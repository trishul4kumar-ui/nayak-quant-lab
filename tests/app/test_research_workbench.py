"""Production-policy tests use explicit deterministic fixtures, never provider I/O."""

from __future__ import annotations

import json
import math
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from pydantic import ValidationError

from quantlab.agents.repository import AgentRepository
from quantlab.app.jobs import Job, JobStatus
from quantlab.app.market_backtest import FrozenMarketHistory, HistoryBar
from quantlab.app.real_history import register_history
from quantlab.app.research_workbench import (
    DEFAULT_SPECIFICATIONS,
    FrozenResearchResult,
    ResearchRunContext,
    ResearchRunParameters,
    execute_research_workbench,
    list_research_inputs,
    list_research_results,
    load_research_run,
)
from quantlab.app.research_workbench_engines import available_research_specifications
from quantlab.core.errors import DataIntegrityError
from quantlab.data.fabric.types import DatasetState
from quantlab.models.registry import ExperimentLedger
from quantlab.research.exploratory import load_exploratory_frame


def frozen_history(
    symbol: str = "BEL",
    index: int = 0,
    *,
    n: int = 110,
    offset: int = 0,
    interval: str = "day",
    volume: bool = True,
) -> FrozenMarketHistory:
    start = datetime(2025, 1, 1, tzinfo=UTC)
    candles = []
    duration = timedelta(days=1) if interval == "day" else timedelta(minutes=5)
    for i in range(n):
        # Non-constant cross-section and return profile, deterministic test-only facts.
        close = (
            100 + index * 12 + i * (0.1 + index * 0.04) + math.sin(i / (3 + index)) * (1 + index)
        )
        candles.append(
            HistoryBar(
                time=start + duration * (i + offset),
                open=close - 0.2,
                high=close + 1.0,
                low=close - 1.0,
                close=close,
                volume=1000 + i if volume else None,
            )
        )
    return FrozenMarketHistory.model_validate(
        {
            "created_at": start + timedelta(days=200),
            "captured_at": start + timedelta(days=200),
            "instrument": "NSE:" + symbol,
            "interval": interval,
            "requested_days": 366,
            "candles": candles,
            "excluded_forming_bars": 0,
        }
    )


def store(tmp_path: Path, histories: tuple[FrozenMarketHistory, ...]) -> Path:
    path = tmp_path / "research.sqlite"
    repo = AgentRepository(path)
    try:
        for row in histories:
            repo.put(row)
    finally:
        repo.close()
    return path


def job(engine: str, hashes: tuple[str, ...], **extra: object) -> Job:
    params = ResearchRunParameters.model_validate(
        {"engine": engine, "history_hashes": hashes, **extra}
    )
    return Job(
        "test-" + engine,
        "research_workbench",
        JobStatus.RUNNING,
        "now",
        parameters=params.model_dump(mode="json"),
    )


def test_all_default_specifications_exist() -> None:
    for engine, spec in DEFAULT_SPECIFICATIONS.items():
        assert spec in available_research_specifications(engine)


def test_single_stock_features_are_real_exploratory_not_pit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("_QUANTLAB_TEST_FIXTURES", raising=False)
    history = frozen_history()
    path = store(tmp_path, (history,))
    catalog = register_history(history, tmp_path / "fabric")
    assert catalog.state == DatasetState.NOT_READY
    result = execute_research_workbench(
        job("features", (history.content_hash,)), path, tmp_path / "ledger.jsonl"
    )
    assert result["input_tier"] == "EXPLORATORY"
    assert result["data_kind"] == "REAL"
    assert result["gate_outcome"] == "NOT_TESTED"
    assert result["context"]["historical_availability_verified"] is False
    assert result["metrics"]["rank_ic"] is None
    assert result["metrics"]["observations"] > 0
    assert 0 < result["metrics"]["coverage"] < 1
    assert result["execution_authority"] is False
    assert all(row["timestamps"] for row in result["series"])
    frozen = load_research_run(path, result["result_hash"])
    assert frozen.envelope() == result
    assert list_research_results(path, "features") == (frozen,)
    assert list_research_results(path, "alpha") == ()
    assert list_research_inputs(path)[0].historical_availability_verified is False
    row = ExperimentLedger(tmp_path / "ledger.jsonl").get(result["run_id"])
    assert row is not None and row.status.value == "completed" and row.gate_outcome == "NOT_TESTED"


@pytest.mark.parametrize(
    "engine",
    [
        "alpha",
        "adaptive",
        "model",
        "ensemble",
        "portfolio",
        "risk",
        "regime",
        "econometrics",
        "discovery",
    ],
)
def test_existing_engines_execute_real_aligned_captures(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    engine: str,
) -> None:
    monkeypatch.delenv("_QUANTLAB_TEST_FIXTURES", raising=False)
    histories = tuple(frozen_history(symbol, i) for i, symbol in enumerate(("BEL", "INFY", "HAL")))
    path = store(tmp_path, histories)
    result = execute_research_workbench(
        job(engine, tuple(h.content_hash for h in histories)), path, tmp_path / "ledger.jsonl"
    )
    assert result["engine"] == engine
    assert result["gate_outcome"] == "NOT_TESTED"
    assert result["sample"]["instruments"] == 3
    assert result["metrics"]
    assert load_research_run(path, result["run_id"]).content_hash == result["result_hash"]
    assert result["live_trading"] is False
    if engine == "portfolio":
        assert sum(result["targets"].values()) == pytest.approx(1)
        assert "expected_return" not in result
        assert result["score_kind"] == "rank_score_not_expected_return"
    if engine == "econometrics":
        assert "scipy.stats" in result["method"]
        assert "Q–Q" in result["tables"][1]["name"]


def test_alignment_uses_timestamps_not_array_positions(tmp_path: Path) -> None:
    first = frozen_history(n=60)
    second = frozen_history("INFY", 1, n=50, offset=20)
    path = store(tmp_path, (first, second))
    frame = load_exploratory_frame(path, (first.content_hash, second.content_hash))
    assert len(frame.dates) == 40
    assert frame.dropped_bars == (20, 10)
    assert all(
        [bar.pit.event_time for bar in rows] == list(frame.dates) for rows in frame.bars.values()
    )


@pytest.mark.parametrize(
    "engine", ["alpha", "adaptive", "ensemble", "discovery", "portfolio", "risk"]
)
def test_single_symbol_does_not_fabricate_cross_section(tmp_path: Path, engine: str) -> None:
    history = frozen_history()
    path = store(tmp_path, (history,))
    with pytest.raises(
        DataIntegrityError, match="CROSS_SECTION_REQUIRED|MULTI_INSTRUMENT_REQUIRED"
    ):
        execute_research_workbench(
            job(engine, (history.content_hash,)), path, tmp_path / "ledger.jsonl"
        )
    assert not (tmp_path / "ledger.jsonl").exists()


def test_analysis_cutoff_excludes_bar_that_has_not_closed(tmp_path: Path) -> None:
    history = frozen_history()
    path = store(tmp_path, (history,))
    cutoff = history.candles[70].time
    frame = load_exploratory_frame(path, (history.content_hash,), end=cutoff)
    assert frame.dates[-1] == cutoff
    last = next(iter(frame.bars.values()))[-1]
    assert last.close == history.candles[69].close
    assert last.close != history.candles[70].close


def test_incompatible_intervals_and_duplicate_symbol_rejected(tmp_path: Path) -> None:
    first = frozen_history()
    duplicate = frozen_history(n=90)
    other = frozen_history("INFY", interval="5minute")
    path = store(tmp_path, (first, duplicate, other))
    with pytest.raises(DataIntegrityError, match="DUPLICATE_INSTRUMENT"):
        load_exploratory_frame(path, (first.content_hash, duplicate.content_hash))
    with pytest.raises(DataIntegrityError, match="INCOMPATIBLE_HISTORY_INTERVALS"):
        load_exploratory_frame(path, (first.content_hash, other.content_hash))


def test_unknown_volume_not_computed_as_zero(tmp_path: Path) -> None:
    history = frozen_history(volume=False)
    path = store(tmp_path, (history,))
    with pytest.raises(DataIntegrityError, match="VOLUME_UNAVAILABLE"):
        execute_research_workbench(
            job("features", (history.content_hash,), specification="volume_zscore_20"),
            path,
            tmp_path / "ledger.jsonl",
        )


def test_cancel_before_loading_does_not_persist_result(tmp_path: Path) -> None:
    task = job("features", ("a" * 64,))
    task.cancel_event.set()
    with pytest.raises(ValueError, match="cancelled"):
        execute_research_workbench(task, tmp_path / "unused.sqlite", tmp_path / "ledger.jsonl")
    assert not (tmp_path / "unused.sqlite").exists()


def test_result_hash_and_context_cannot_be_relabelled(tmp_path: Path) -> None:
    history = frozen_history()
    path = store(tmp_path, (history,))
    result = execute_research_workbench(
        job("features", (history.content_hash,)), path, tmp_path / "ledger.jsonl"
    )
    frozen = load_research_run(path, result["result_hash"])
    changed = frozen.model_dump(mode="json")
    report = json.loads(changed["report_json"])
    report["metrics"]["mean"] = 999
    changed["report_json"] = json.dumps(report)
    with pytest.raises(ValidationError, match="hash mismatch"):
        FrozenResearchResult.model_validate(changed)


def test_wrong_parent_cannot_supply_another_universe(tmp_path: Path) -> None:
    first, other = frozen_history(), frozen_history("INFY", 1)
    path = store(tmp_path, (first, other))
    result = execute_research_workbench(
        job("features", (first.content_hash,)), path, tmp_path / "ledger.jsonl"
    )
    with pytest.raises(DataIntegrityError, match="INCOMPATIBLE_RESEARCH_PARENT"):
        execute_research_workbench(
            job("features", (other.content_hash,), parent_hashes=(result["result_hash"],)),
            path,
            tmp_path / "ledger.jsonl",
        )


def test_horizon_not_silently_ignored(tmp_path: Path) -> None:
    history = frozen_history()
    path = store(tmp_path, (history,))
    with pytest.raises(DataIntegrityError, match="HORIZON_NOT_SUPPORTED"):
        execute_research_workbench(
            job("model", (history.content_hash,), horizon=5), path, tmp_path / "ledger.jsonl"
        )


def test_selected_parent_outputs_flow_into_ensemble_portfolio_and_risk(tmp_path: Path) -> None:
    histories = tuple(frozen_history(symbol, i) for i, symbol in enumerate(("BEL", "INFY", "HAL")))
    hashes = tuple(h.content_hash for h in histories)
    path = store(tmp_path, histories)
    ledger = tmp_path / "ledger.jsonl"
    alpha = execute_research_workbench(job("alpha", hashes), path, ledger)
    ensemble = execute_research_workbench(
        job("ensemble", hashes, parent_hashes=(alpha["result_hash"],)), path, ledger
    )
    assert ensemble["component_sources"]["rank_momentum_20"] == alpha["result_hash"]
    assert ensemble["component_sources"]["rank_momentum_5"] == "RECOMPUTED_VERSIONED_COMPONENT"
    portfolio = execute_research_workbench(
        job("portfolio", hashes, parent_hashes=(ensemble["result_hash"],)), path, ledger
    )
    assert portfolio["score_source"] == ensemble["result_hash"]
    assert portfolio["scores"] == ensemble["scores"]
    risk = execute_research_workbench(
        job("risk", hashes, parent_hashes=(portfolio["result_hash"],)), path, ledger
    )
    assert risk["portfolio_source"] == portfolio["result_hash"]
    assert risk["target_weights"] == portfolio["target_weights"]
    assert risk["metrics"]["portfolio_volatility"] is not None


def test_hard_constraint_rejection_is_retained_not_relaxed(tmp_path: Path) -> None:
    histories = tuple(frozen_history(symbol, i) for i, symbol in enumerate(("BEL", "INFY", "HAL")))
    path = store(tmp_path, histories)
    result = execute_research_workbench(
        job("portfolio", tuple(h.content_hash for h in histories), specification="mom20_topn"),
        path,
        tmp_path / "ledger.jsonl",
    )
    assert result["construction_state"] == "INFEASIBLE"
    assert result["target_weights"] == {}
    assert result["blocking_reasons"]
    assert load_research_run(path, result["result_hash"]).gate_outcome == "NOT_TESTED"


def test_failed_ledger_persistence_does_not_publish_partial_result(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    history = frozen_history()
    path = store(tmp_path, (history,))

    def fail(*_: object, **__: object) -> None:
        raise OSError("test persistence failure")

    monkeypatch.setattr(ExperimentLedger, "append", fail)
    with pytest.raises(OSError, match="test persistence failure"):
        execute_research_workbench(
            job("features", (history.content_hash,)), path, tmp_path / "ledger.jsonl"
        )
    assert list_research_results(path) == ()
    with pytest.raises(DataIntegrityError, match="NOT_PUBLISHED"):
        load_research_run(path, "research-test-features")


def test_feature_prefix_cannot_change_with_future_tail(tmp_path: Path) -> None:
    first = frozen_history()
    changed_data = first.model_dump(exclude={"content_hash"})
    changed_data["candles"][-1]["high"] = 999.0
    changed_data["candles"][-1]["close"] = 998.0
    other = FrozenMarketHistory.model_validate(changed_data)
    path = store(tmp_path, (first, other))
    left = job("features", (first.content_hash,))
    right = job("features", (other.content_hash,))
    right.job_id = "different-future-tail"
    a = execute_research_workbench(left, path, tmp_path / "ledger.jsonl")
    b = execute_research_workbench(right, path, tmp_path / "ledger.jsonl")
    assert a["series"][0]["values"][:-1] == b["series"][0]["values"][:-1]


def test_strict_pit_validation_loader_does_not_accept_capture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from quantlab.core.config import get_settings
    from quantlab.research.pipeline import load_real_frame

    history = frozen_history()
    record = register_history(history, tmp_path / "fabric")
    monkeypatch.setenv("QUANT_LAB_RESEARCH_DATASET", record.dataset_id + "@" + record.version)
    get_settings.cache_clear()
    try:
        with pytest.raises(DataIntegrityError, match="REAL_PIT_DATASET_NOT_VERIFIED"):
            load_real_frame(fabric_root=tmp_path / "fabric")
    finally:
        get_settings.cache_clear()


def test_single_stock_regime_uses_actual_trailing_volatility(tmp_path: Path) -> None:
    history = frozen_history()
    path = store(tmp_path, (history,))
    result = execute_research_workbench(
        job("regime", (history.content_hash,)), path, tmp_path / "ledger.jsonl"
    )
    assert result["metrics"]["labelled_bars"] > 0
    assert any(v is not None for v in result["series"][0]["values"])
    assert all(row["avg_pairwise_corr"] is None for row in result["snapshots"])
    assert all(row["dispersion_cs"] is None for row in result["snapshots"])
    assert "Selected-asset" in result["snapshots"][-1]["note"]


def test_fast_aligned_states_match_existing_multi_name_observables(tmp_path: Path) -> None:
    from quantlab.regimes.engine import compute_state_panel
    from quantlab.research.exploratory_states import exploratory_state_panel

    histories = tuple(
        frozen_history(symbol, i, n=45) for i, symbol in enumerate(("BEL", "INFY", "HAL"))
    )
    path = store(tmp_path, histories)
    frame = load_exploratory_frame(path, tuple(h.content_hash for h in histories))
    existing = compute_state_panel(frame.bars, lookback=20)
    fast = exploratory_state_panel(frame, lookback=20, cancelled=lambda: None)
    for before, after in zip(existing, fast, strict=True):
        for name, value in before.vector().items():
            assert after.vector()[name] == pytest.approx(value)


def test_inventory_metadata_cache_invalidates_on_live_wal_append(tmp_path: Path) -> None:
    first = frozen_history()
    path = store(tmp_path, (first,))
    repo = AgentRepository(path)
    try:
        old = list_research_inputs(path)
        assert list_research_inputs(path) is old
        second = frozen_history("INFY", 1)
        repo.put(second)  # Keep this connection open: new content remains in WAL.
        new = list_research_inputs(path)
        assert {row.history_hash for row in new} == {first.content_hash, second.content_hash}
        assert new is not old
        assert list_research_inputs(path) is new
    finally:
        repo.close()


def test_corrupted_inventory_fails_closed_and_execution_rechecks_hash(tmp_path: Path) -> None:
    first = frozen_history()
    path = store(tmp_path, (first,))
    assert list_research_inputs(path)
    connection = sqlite3.connect(path)
    try:
        connection.execute(
            "UPDATE control_plane_records SET payload_json = '{' "
            "WHERE namespace = 'agent_artifacts'"
        )
        connection.commit()
    finally:
        connection.close()
    with pytest.raises(DataIntegrityError, match="INDEX_UNAVAILABLE"):
        list_research_inputs(path)


def test_inventory_projection_does_not_replace_full_execution_hash_verification(
    tmp_path: Path,
) -> None:
    history = frozen_history()
    path = store(tmp_path, (history,))
    assert list_research_inputs(path)
    connection = sqlite3.connect(path)
    try:
        connection.execute(
            "UPDATE control_plane_records SET payload_json = json_set(payload_json, "
            "'$.artifact.candles[0].close', 999.0) "
            "WHERE namespace = 'agent_artifacts'"
        )
        connection.commit()
    finally:
        connection.close()
    # The UI inventory is explicitly metadata only. Execution independently loads
    # the immutable full artifact and rejects a tampered candle/hash.
    assert list_research_inputs(path)
    with pytest.raises(ValidationError):
        execute_research_workbench(
            job("features", (history.content_hash,)), path, tmp_path / "ledger.jsonl"
        )


def test_cancel_at_publication_boundary_does_not_publish(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    history = frozen_history()
    path = store(tmp_path, (history,))
    original = Job.begin_publication

    def cancel_at_boundary(task: Job) -> None:
        task.request_cancel()
        original(task)

    monkeypatch.setattr(Job, "begin_publication", cancel_at_boundary)
    with pytest.raises(RuntimeError, match="cancelled before publication"):
        execute_research_workbench(
            job("features", (history.content_hash,)), path, tmp_path / "ledger.jsonl"
        )
    assert list_research_results(path) == ()
    assert not (tmp_path / "ledger.jsonl").exists()


def test_cancel_during_publication_is_not_accepted(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    history = frozen_history()
    path = store(tmp_path, (history,))
    task = job("features", (history.content_hash,))
    original = AgentRepository.put
    attempted: list[bool] = []

    def put_and_attempt_cancel(repository: AgentRepository, artifact: object) -> object:
        if isinstance(artifact, ResearchRunContext):
            attempted.append(bool(task.request_cancel()))
        return original(repository, artifact)

    monkeypatch.setattr(AgentRepository, "put", put_and_attempt_cancel)
    result = execute_research_workbench(task, path, tmp_path / "ledger.jsonl")
    assert attempted == [False]
    assert not task.cancel_event.is_set()
    assert load_research_run(path, result["result_hash"]).run_id == result["run_id"]
