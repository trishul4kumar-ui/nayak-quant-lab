from __future__ import annotations

import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, date, datetime
from pathlib import Path
from threading import Barrier

import pytest
from tests.app.test_strategy_research import ProposalProvider, execute

from quantlab.agents.repository import AgentRepository
from quantlab.app import strategy_research as engine
from quantlab.app.strategy_research import (
    FrozenStrategyBatch,
    StrategyHistoryExposure,
    load_strategy_batch,
)
from quantlab.core.errors import DataIntegrityError
from quantlab.models.registry import ExperimentLedger


def _claim(
    batch: str, *, interval: str = "day", instrument: str = "NSE:INFY"
) -> StrategyHistoryExposure:
    return StrategyHistoryExposure(
        batch_id=batch,
        instrument=instrument,
        interval=interval,
        history_hash="a" * 64,
        kind="holdout",
        start_day=date(2025, 4, 1),
        end_day=date(2025, 4, 5),
    )


def test_concurrent_holdouts_see_each_other_atomically(tmp_path: Path) -> None:
    path = tmp_path / "agents.sqlite"
    # Initialize the schema before the workers compete to reserve an interval.
    AgentRepository(path).close()
    start = Barrier(2)

    def reserve(batch: str, interval: str) -> bool:
        repo = AgentRepository(path)
        try:
            start.wait(timeout=5)
            return engine._record_history_exposure(repo, _claim(batch, interval=interval))
        finally:
            repo.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(reserve, "batch-a", "day")
        second = pool.submit(reserve, "batch-b", "5minute")
        assert sorted([first.result(timeout=10), second.result(timeout=10)]) == [False, True]


def test_distinct_instruments_do_not_collide(tmp_path: Path) -> None:
    repo = AgentRepository(tmp_path / "agents.sqlite")
    try:
        assert not engine._record_history_exposure(repo, _claim("first"))
        assert not engine._record_history_exposure(repo, _claim("second", instrument="NSE:TCS"))
    finally:
        repo.close()


def test_prior_training_and_different_interval_contaminate_same_days(tmp_path: Path) -> None:
    repo = AgentRepository(tmp_path / "agents.sqlite")
    try:
        training = _claim("prior", interval="5minute").model_copy(
            update={"kind": "training_validation"}
        )
        assert not engine._record_history_exposure(repo, training)
        assert engine._record_history_exposure(repo, _claim("later", interval="day"))
    finally:
        repo.close()


def test_failure_after_holdout_cannot_erase_its_exposure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    with monkeypatch.context() as patch:
        def fail_publication(*args: object, **kwargs: object) -> None:
            raise OSError("LEDGER_FAILED")

        patch.setattr(ExperimentLedger, "append", fail_publication)
        with pytest.raises(OSError, match="LEDGER_FAILED"):
            execute(tmp_path)
    result = execute(tmp_path)
    assert result["holdout"] is not None
    assert result["holdout_reused"] is True
    assert any("HOLDOUT_REUSED" in warning for warning in result["warnings"])


def test_failed_holdout_attempt_remains_exposed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = engine.calculate_market_backtest

    def fail_holdout(history, params, **kwargs):  # type: ignore[no-untyped-def]
        if kwargs["end_index"] == len(history.candles):
            raise ValueError("simulated holdout failure")
        return original(history, params, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(engine, "calculate_market_backtest", fail_holdout)
        report = execute(tmp_path)
    assert report["holdout"] is None
    assert any("HOLDOUT_UNAVAILABLE" in warning for warning in report["warnings"])
    assert execute(tmp_path)["holdout_reused"] is True


def test_training_data_is_claimed_even_if_provider_fails(tmp_path: Path) -> None:
    provider = ProposalProvider()
    provider.raw = '{"candidates": [{"code": "invalid"}]}'
    with pytest.raises(Exception, match="INVALID_STRUCTURED_OUTPUT"):
        execute(tmp_path, provider=provider)
    with sqlite3.connect(tmp_path / "agents.sqlite") as connection:
        rows = connection.execute(
            "SELECT payload_json FROM control_plane_records WHERE namespace = ?",
            ("strategy_history_exposure",),
        ).fetchall()
    assert len(rows) == 1 and '"training_validation"' in rows[0][0]


def test_corrupt_prior_claim_prevents_holdout_assumptions(tmp_path: Path) -> None:
    path = tmp_path / "agents.sqlite"
    repo = AgentRepository(path)
    engine._record_history_exposure(repo, _claim("first"))
    repo.close()
    with sqlite3.connect(path) as connection:
        connection.execute(
            "UPDATE control_plane_records SET payload_json = ? WHERE namespace = ?",
            ('{"bad": true}', "strategy_history_exposure"),
        )
    repo = AgentRepository(path)
    try:
        with pytest.raises(DataIntegrityError, match="STRATEGY_EXPOSURE_LEDGER_INVALID"):
            engine._record_history_exposure(repo, _claim("second"))
    finally:
        repo.close()


@pytest.mark.parametrize("tamper", ["flag", "warning", "downgrade"])
def test_resealed_report_cannot_suppress_reuse_warning(tmp_path: Path, tamper: str) -> None:
    execute(tmp_path)
    result = execute(tmp_path)
    assert result["holdout_reused"] is True
    path = tmp_path / "agents.sqlite"
    original = load_strategy_batch(path, result["result_hash"])
    report = json.loads(original.report_json)
    if tamper == "flag":
        report["holdout_reused"] = False
    elif tamper == "warning":
        report["warnings"] = [w for w in report["warnings"] if not w.startswith("HOLDOUT_REUSED:")]
    else:
        del report["context"]["exposure_ledger_version"]
    content = original.model_dump(mode="json", exclude={"content_hash"})
    content["report_json"] = json.dumps(report, sort_keys=True, allow_nan=False)
    forged = FrozenStrategyBatch.model_validate(content)
    repo = AgentRepository(path)
    try:
        repo.put(forged)
        repo.audit(
            "STRATEGY_BATCH_COMPLETED", run_id=forged.batch_id,
            now=datetime.now(UTC), artifact_hash=forged.content_hash,
        )
    finally:
        repo.close()
    with pytest.raises(ValueError, match="STRATEGY_BATCH_EXPOSURE_BINDING_MISMATCH"):
        load_strategy_batch(path, forged.content_hash)


def test_deleted_prior_audit_fails_closed_on_report_reopen(tmp_path: Path) -> None:
    execute(tmp_path)
    result = execute(tmp_path)
    path = tmp_path / "agents.sqlite"
    with sqlite3.connect(path) as connection:
        connection.execute(
            "DELETE FROM control_plane_audit WHERE namespace = ? AND identity LIKE ?",
            ("strategy_history_exposure", "%:holdout"),
        )
    with pytest.raises(Exception, match="AGENT_PERSISTENCE_UNAVAILABLE"):
        load_strategy_batch(path, result["result_hash"])


def test_legacy_saved_report_still_marks_later_overlap(tmp_path: Path) -> None:
    execute(tmp_path)
    path = tmp_path / "agents.sqlite"
    # Emulate a store whose earlier report predates the exposure ledger.
    with sqlite3.connect(path) as connection:
        connection.execute(
            "DELETE FROM control_plane_records WHERE namespace = ?", ("strategy_history_exposure",)
        )
        connection.execute(
            "DELETE FROM control_plane_audit WHERE namespace = ?", ("strategy_history_exposure",)
        )
    result = execute(tmp_path)
    assert result["holdout_reused"] is True


def test_legacy_training_and_warmup_are_not_untouched_holdouts(tmp_path: Path) -> None:
    result = execute(tmp_path)
    context = result["context"]
    train_day = datetime.fromisoformat(context["train_start"]).date()
    old_holdout_day = datetime.fromisoformat(context["holdout_start"]).date()
    assert train_day < old_holdout_day
    repo = AgentRepository(tmp_path / "agents.sqlite")
    try:
        assert engine._legacy_holdout_overlap(
            repo, instrument="NSE:INFY", start_day=train_day, end_day=train_day
        )
        # The whole frozen history includes feature warm-up before train_start.
        assert engine._legacy_holdout_overlap(
            repo, instrument="NSE:INFY", start_day=date(2025, 1, 1), end_day=date(2025, 1, 1)
        )
    finally:
        repo.close()


def test_legacy_missing_history_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    execute(tmp_path)
    repo = AgentRepository(tmp_path / "agents.sqlite")
    try:
        def missing(*args: object, **kwargs: object) -> None:
            raise KeyError("missing")

        monkeypatch.setattr(repo, "get", missing)
        with pytest.raises(DataIntegrityError, match="STRATEGY_LEGACY_EXPOSURE_UNKNOWN"):
            engine._legacy_holdout_overlap(
                repo, instrument="NSE:INFY", start_day=date(2025, 4, 1), end_day=date(2025, 4, 2)
            )
    finally:
        repo.close()
