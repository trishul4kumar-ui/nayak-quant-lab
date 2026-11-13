"""Software contract fixtures only; these are not live provider acceptance tests."""

from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from quantlab.agents.repository import AgentRepository
from quantlab.app.jobs import Job, JobStatus
from quantlab.app.market_backtest import FrozenMarketHistory, HistoryBar
from quantlab.app.paper_workflow import (
    FrozenPaperWorkflowRun,
    PaperWorkflowInputs,
    allocate_research_capital,
    execute_paper_workflow,
    load_workflow,
    prepare_workflow,
    restore_paper_checkpoint,
)
from quantlab.app.research_workbench import (
    FrozenResearchResult,
    ResearchRunContext,
    ResearchRunParameters,
)
from quantlab.core.errors import DataIntegrityError
from quantlab.monitoring.state import reset as reset_monitor
from quantlab.paper_oms.state import reset as reset_paper
from quantlab.shadow.state import reset as reset_shadow
from quantlab.tca.state import reset as reset_tca


@pytest.fixture(autouse=True)
def _production_policy(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("_QUANTLAB_TEST_FIXTURES", raising=False)
    reset_monitor()
    reset_paper()
    reset_shadow()
    reset_tca()


def _histories(repository: AgentRepository, *, additional_bar: bool = False) -> tuple[str, ...]:
    start = datetime(2024, 1, 8, tzinfo=UTC)
    captured = datetime(2024, 1, 18, tzinfo=UTC)
    return tuple(
        repository.put(
            FrozenMarketHistory(
                created_at=captured,
                captured_at=captured,
                instrument=name,
                interval="day",
                requested_days=31,
                excluded_forming_bars=0,
                candles=tuple(
                    HistoryBar(
                        time=start + timedelta(days=index),
                        open=100 + index * 2 + offset,
                        high=105 + index * 2 + offset,
                        low=95 + index * 2 + offset,
                        close=103 + index * 2 + offset,
                        volume=100000.0,
                    )
                    for index in range(10 if additional_bar else 9)
                ),
            )
        ).content_hash
        for name, offset in (("NSE:AAA", 0), ("NSE:BBB", 30))
    )


def _research(repository_path: Path) -> tuple[str, tuple[str, ...]]:
    repository = AgentRepository(repository_path)
    try:
        hashes = _histories(repository)
        time = datetime(2024, 1, 16, tzinfo=UTC)
        parameters = ResearchRunParameters(engine="portfolio", history_hashes=hashes)
        context = repository.put(
            ResearchRunContext(
                created_at=time,
                run_id="contract-portfolio-1",
                correlation_id="contract-job-1",
                parameters=parameters,
                input_hash="c" * 64,
                history_hashes=hashes,
                universe=("NSE:AAA", "NSE:BBB"),
                interval="day",
                aligned_bars=8,
                analytical_start=datetime(2024, 1, 9, tzinfo=UTC),
                analytical_end=time,
                captured_at=(datetime(2024, 1, 18, tzinfo=UTC),) * 2,
                dropped_bars=(0, 0),
            )
        )
        result = repository.put(
            FrozenResearchResult(
                created_at=time,
                run_id=context.run_id,
                engine="portfolio",
                specification="mom20_topn",
                context=context,
                report_json=json.dumps(
                    {
                        "target_weights": {"NSE:AAA": 0.4, "NSE:BBB": 0.6},
                        "scores": {"NSE:AAA": 0.2, "NSE:BBB": 0.8},
                        "score_kind": "rank_score_not_expected_return",
                        "covariance": {
                            "names": ["NSE:AAA", "NSE:BBB"],
                            "matrix": [[0.0004, 0.0001], [0.0001, 0.0009]],
                            "lookback": 7,
                            "n_obs": 7,
                            "as_of": time.isoformat(),
                            "psd": True,
                            "status": "pass",
                            "note": "per-interval contract fixture",
                        },
                    }
                ),
            )
        )
        repository.audit(
            "RESEARCH_COMPLETED", run_id=result.run_id, now=time, artifact_hash=result.content_hash
        )
        return result.content_hash, hashes
    finally:
        repository.close()


def _job(kind: str, workflow_id: str, **parameters: object) -> Job:
    return Job(
        job_id=f"contract-{kind}",
        type="paper_workflow",
        status=JobStatus.RUNNING,
        created_at=datetime.now(UTC).isoformat(),
        parameters={"kind": kind, "workflow_id": workflow_id, **parameters},
    )


def test_no_inputs_are_actionable_not_seed_fallback(tmp_path: Path) -> None:
    from quantlab.app import monitoring, paper_oms, shadow, tca

    for action in (
        lambda: paper_oms.submit_payload("last"),
        monitoring.run_payload,
        tca.run_payload,
        shadow.run_payload,
    ):
        with pytest.raises(DataIntegrityError, match="WORKFLOW_INPUTS_REQUIRED"):
            action()
    with pytest.raises(DataIntegrityError, match="PAPER_ACCOUNT_CONFIG_REQUIRED"):
        paper_oms.create_payload()


def test_constructor_budget_is_not_rank_as_expected_return(tmp_path: Path) -> None:
    path = tmp_path / "agents.sqlite"
    research, _ = _research(path)
    blocked = allocate_research_capital(
        repository_path=path,
        ledger_path=tmp_path / "ledger.jsonl",
        research_result_hash=research,
        opening_cash=100000,
    )
    assert blocked["decision"]["abstention_code"] == "unknown_liquidity"
    result = allocate_research_capital(
        repository_path=path,
        ledger_path=tmp_path / "ledger.jsonl",
        research_result_hash=research,
        opening_cash=100000,
        allow_unverified_liquidity=True,
    )
    assert result["decision"]["expected_return"] == {}
    assert result["decision"]["decision_status"] == "research_only"
    assert sum(result["target"]["weights"].values()) == pytest.approx(0.95)
    assert result["target"]["cash_target"] == pytest.approx(5000)
    assert result["decision"]["liquidity_status"] == "unknown"


def test_explicit_chain_paper_monitor_tca_shadow_and_uncached_replay(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path, ledger = tmp_path / "agents.sqlite", tmp_path / "ledger.jsonl"
    research, histories = _research(path)
    prepared = prepare_workflow(
        repository_path=path,
        ledger_path=ledger,
        research_result_hash=research,
        opening_cash=100000,
        reviewed=True,
        allow_unverified_liquidity=True,
    )
    workflow = prepared["workflow_id"]
    repository = AgentRepository(path)
    try:
        inputs = load_workflow(repository, workflow)
        assert isinstance(inputs, PaperWorkflowInputs)
        assert inputs.arrival.history_hashes == histories
        assert inputs.arrival.snapshot.as_of > inputs.decision.decision_time
        later = _histories(repository, additional_bar=True)
    finally:
        repository.close()
    paper = execute_paper_workflow(
        _job("paper_oms", workflow), repository_path=path, ledger_path=ledger
    )
    assert paper["result"]["run"]["fill_count"] > 0
    assert paper["live_trading"] is False
    assert paper["historical_replay"] is True
    tca = execute_paper_workflow(_job("tca", workflow), repository_path=path, ledger_path=ledger)
    assert tca["result"]["paper_comparison"]["target_notional"] == pytest.approx(95000)
    monitoring = execute_paper_workflow(
        _job("monitoring", workflow, mark_history_hashes=later),
        repository_path=path,
        ledger_path=ledger,
    )
    assert monitoring["result"]["snapshot"]["as_of"] > prepared["as_of"]
    assert monitoring["result"]["reconciliation_ok"] is True
    shadow = execute_paper_workflow(
        _job("shadow", workflow), repository_path=path, ledger_path=ledger
    )
    assert shadow["result"]["broker_routing_enabled"] is False
    assert shadow["result"]["freshness"]["clock_kind"] == "historical_replay_assumption"
    capture_time = inputs.arrival.snapshot.captured_at
    assert capture_time is not None
    assert (
        datetime.fromisoformat(shadow["result"]["freshness"]["source_captured_at"]) == capture_time
    )
    from quantlab.app.shadow import last_run_row

    monkeypatch.setattr(
        "quantlab.app.paper_workflow.latest_workflow_result",
        lambda *_args, **_kwargs: {**shadow["result"], "workflow_id": workflow},
    )
    row = last_run_row()
    assert row is not None
    assert {"id", "mode", "status", "recon", "orders", "fills", "hash"}.issubset(row)
    replay = execute_paper_workflow(
        _job("twin", workflow), repository_path=path, ledger_path=ledger
    )
    assert replay["result"]["replay_status"] == "MATCH"
    assert replay["result"]["checks"]["fills"] is True


def _published_checkpoint(tmp_path: Path) -> tuple[Path, dict[str, Any], tuple[str, ...]]:
    path, ledger = tmp_path / "agents.sqlite", tmp_path / "ledger.jsonl"
    research, histories = _research(path)
    prepared = prepare_workflow(
        repository_path=path,
        research_result_hash=research,
        opening_cash=100000,
        reviewed=True,
        allow_unverified_liquidity=True,
    )
    result = execute_paper_workflow(
        _job("paper_oms", prepared["workflow_id"]), repository_path=path, ledger_path=ledger
    )
    return path, result, histories


def test_paper_checkpoint_restores_in_fresh_process_without_new_fills(tmp_path: Path) -> None:
    path, result, _ = _published_checkpoint(tmp_path)
    program = """
import json, sys
from pathlib import Path
from quantlab.agents.repository import AgentRepository
from quantlab.app.paper_workflow import restore_paper_checkpoint
r = AgentRepository(Path(sys.argv[1]))
try:
    inputs, paper = restore_paper_checkpoint(r, sys.argv[2], sys.argv[3])
    print(json.dumps({'workflow': inputs.content_hash, 'result': paper.model_dump(mode='json')}))
finally:
    r.close()
"""
    with sqlite3.connect(path) as connection:
        before = connection.execute("SELECT COUNT(*) FROM control_plane_records").fetchone()
    restored = subprocess.run(
        [sys.executable, "-c", program, str(path), result["workflow_id"], result["result_hash"]],
        check=True,
        capture_output=True,
        text=True,
    )
    output = json.loads(restored.stdout)
    assert output["workflow"] == result["workflow_id"]
    assert output["result"] == result["result"]
    with sqlite3.connect(path) as connection:
        after = connection.execute("SELECT COUNT(*) FROM control_plane_records").fetchone()
    assert after == before


@pytest.mark.parametrize("damage", ["missing_run", "corrupt_run", "missing_history", "unpublished"])
def test_paper_checkpoint_rejects_missing_corrupt_or_unpublished_state(
    tmp_path: Path, damage: str
) -> None:
    path, result, histories = _published_checkpoint(tmp_path)
    with sqlite3.connect(path) as connection:
        if damage == "corrupt_run":
            connection.execute(
                "UPDATE control_plane_records SET payload_json = replace(payload_json, "
                "'Paper OMS result.', 'Tampered OMS result.') WHERE namespace = ? AND identity = ?",
                ("agent_artifacts", result["result_hash"]),
            )
        elif damage == "unpublished":
            connection.execute(
                "DELETE FROM control_plane_records WHERE namespace = 'agent_audit' "
                "AND json_extract(payload_json, '$.artifact_hash') = ? "
                "AND json_extract(payload_json, '$.event') = 'PAPER_WORKFLOW_COMPLETED'",
                (result["result_hash"],),
            )
        else:
            identity = histories[0] if damage == "missing_history" else result["result_hash"]
            connection.execute(
                "DELETE FROM control_plane_records WHERE namespace = ? AND identity = ?",
                ("agent_artifacts", identity),
            )
    repository = AgentRepository(path)
    try:
        with pytest.raises((DataIntegrityError, KeyError, ValueError)):
            restore_paper_checkpoint(repository, result["workflow_id"], result["result_hash"])
    finally:
        repository.close()


def test_paper_checkpoint_rejects_resealed_incomplete_result(tmp_path: Path) -> None:
    path, result, _ = _published_checkpoint(tmp_path)
    repository = AgentRepository(path)
    try:
        original = repository.get(result["result_hash"], FrozenPaperWorkflowRun)
        partial = dict(original.result)
        del partial["fills"]
        incomplete = repository.put(
            FrozenPaperWorkflowRun(
                created_at=datetime.now(UTC), kind="paper_oms", workflow_id=result["workflow_id"],
                result=partial,
            )
        )
        repository.audit(
            "PAPER_WORKFLOW_COMPLETED", run_id=result["workflow_id"],
            now=datetime.now(UTC), artifact_hash=incomplete.content_hash,
        )
        with pytest.raises(DataIntegrityError, match="PAPER_CHECKPOINT_INCOMPLETE"):
            restore_paper_checkpoint(repository, result["workflow_id"], incomplete.content_hash)
    finally:
        repository.close()


def test_paper_checkpoint_rejects_resealed_inconsistent_order_count(tmp_path: Path) -> None:
    from quantlab.paper_oms.identity import hash_run
    from quantlab.paper_oms.models import OMSRun

    path, result, _ = _published_checkpoint(tmp_path)
    repository = AgentRepository(path)
    try:
        original = repository.get(result["result_hash"], FrozenPaperWorkflowRun)
        changed = dict(original.result)
        run = OMSRun.model_validate(changed["run"])
        run = run.model_copy(update={"order_count": len(changed["orders"]) + 1})
        run_hash = hash_run(run)
        changed["run"] = run.model_copy(
            update={"run_hash": run_hash, "oms_run_id": f"OMS-{run_hash[:12]}"}
        ).model_dump(mode="json")
        inconsistent = repository.put(
            FrozenPaperWorkflowRun(
                created_at=datetime.now(UTC), kind="paper_oms", workflow_id=result["workflow_id"],
                result=changed,
            )
        )
        repository.audit(
            "PAPER_WORKFLOW_COMPLETED", run_id=result["workflow_id"],
            now=datetime.now(UTC), artifact_hash=inconsistent.content_hash,
        )
        with pytest.raises(DataIntegrityError, match="PAPER_CHECKPOINT_STATE_MISMATCH"):
            restore_paper_checkpoint(repository, result["workflow_id"], inconsistent.content_hash)
    finally:
        repository.close()


def test_downstream_tca_uses_selected_checkpoint_without_fallback(tmp_path: Path) -> None:
    path, original, _ = _published_checkpoint(tmp_path)
    workflow = original["workflow_id"]
    result = execute_paper_workflow(
        _job("tca", workflow, paper_result_hash=original["result_hash"]),
        repository_path=path,
        ledger_path=tmp_path / "ledger.jsonl",
    )
    repository = AgentRepository(path)
    try:
        saved = repository.get(result["result_hash"], FrozenPaperWorkflowRun)
        assert saved.parent_run_hash == original["result_hash"]
    finally:
        repository.close()
    with pytest.raises(DataIntegrityError, match="PAPER_CHECKPOINT_MISSING_OR_CORRUPT"):
        execute_paper_workflow(
            _job("tca", workflow, paper_result_hash="f" * 64),
            repository_path=path,
            ledger_path=tmp_path / "ledger.jsonl",
        )


def test_reject_same_mark_missing_review_and_wrong_parent(tmp_path: Path) -> None:
    path = tmp_path / "agents.sqlite"
    research, histories = _research(path)
    with pytest.raises(DataIntegrityError, match="REVIEW_REQUIRED"):
        prepare_workflow(repository_path=path, research_result_hash=research, opening_cash=10000)
    prepared = prepare_workflow(
        repository_path=path,
        research_result_hash=research,
        opening_cash=10000,
        reviewed=True,
        allow_unverified_liquidity=True,
    )
    execute_paper_workflow(
        _job("paper_oms", prepared["workflow_id"]),
        repository_path=path,
        ledger_path=tmp_path / "ledger.jsonl",
    )
    with pytest.raises(DataIntegrityError, match="SUBSEQUENT_MARK_REQUIRED"):
        execute_paper_workflow(
            _job("monitoring", prepared["workflow_id"], mark_history_hashes=histories),
            repository_path=path,
            ledger_path=tmp_path / "ledger.jsonl",
        )


def test_reconciliation_without_internal_is_unavailable_not_matching(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from quantlab.app.reconciliation import run_payload

    monkeypatch.setattr("quantlab.app.reconciliation.last_snapshot", lambda: None)
    result = run_payload(repository_path=tmp_path / "agents.sqlite")
    assert result["status"] == "BROKER_UNAVAILABLE"
    assert result["internal_snapshot_id"] is None


def test_original_mark_tampering_cannot_be_resealed_as_real(tmp_path: Path) -> None:
    path = tmp_path / "agents.sqlite"
    research, _ = _research(path)
    prepared = prepare_workflow(
        repository_path=path,
        research_result_hash=research,
        opening_cash=10000,
        reviewed=True,
        allow_unverified_liquidity=True,
    )
    repository = AgentRepository(path)
    try:
        original = load_workflow(repository, prepared["workflow_id"])
        changed = original.model_dump(mode="json")
        changed["content_hash"] = ""
        changed["arrival"]["content_hash"] = ""
        changed["arrival"]["snapshot"]["prices"]["NSE:AAA"] = 9999
        forged = repository.put(PaperWorkflowInputs.model_validate(changed))
        with pytest.raises(DataIntegrityError, match="ARRIVAL_SOURCE_BINDING_MISMATCH"):
            load_workflow(repository, forged.content_hash)
    finally:
        repository.close()


def test_failed_publication_cannot_feed_downstream(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from quantlab.app.paper_workflow import latest_workflow_result

    path, ledger = tmp_path / "agents.sqlite", tmp_path / "ledger.jsonl"
    research, _ = _research(path)
    prepared = prepare_workflow(
        repository_path=path,
        ledger_path=ledger,
        research_result_hash=research,
        opening_cash=10000,
        reviewed=True,
        allow_unverified_liquidity=True,
    )

    def fail(*_args: object, **_kwargs: object) -> None:
        raise OSError("contract publication failure")

    monkeypatch.setattr("quantlab.app.paper_workflow._append_workflow_ledger", fail)
    with pytest.raises(OSError, match="publication failure"):
        execute_paper_workflow(
            _job("paper_oms", prepared["workflow_id"]), repository_path=path, ledger_path=ledger
        )
    assert latest_workflow_result("paper_oms", repository_path=path) is None
    with pytest.raises(DataIntegrityError, match="PAPER_RUN_REQUIRED"):
        execute_paper_workflow(
            _job("tca", prepared["workflow_id"]), repository_path=path, ledger_path=ledger
        )


def test_paper_tca_counts_embedded_friction_once(tmp_path: Path) -> None:
    path, ledger = tmp_path / "agents.sqlite", tmp_path / "ledger.jsonl"
    research, _ = _research(path)
    prepared = prepare_workflow(
        repository_path=path,
        ledger_path=ledger,
        research_result_hash=research,
        opening_cash=100000,
        reviewed=True,
        allow_unverified_liquidity=True,
    )
    paper = execute_paper_workflow(
        _job("paper_oms", prepared["workflow_id"]), repository_path=path, ledger_path=ledger
    )
    tca = execute_paper_workflow(
        _job("tca", prepared["workflow_id"]), repository_path=path, ledger_path=ledger
    )
    fills = paper["result"]["fills"]
    displacement = sum(
        abs(fill["execution_price"] - fill["arrival_price"]) * fill["filled_quantity"]
        for fill in fills
    )
    assert tca["result"]["shortfall"]["total"] == pytest.approx(displacement)
    assert all(fill["commission"] == 0 for fill in fills)


def test_internal_import_is_explicit_and_not_broker_copy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from quantlab.app.reconciliation import import_internal_books, run_payload
    from quantlab.broker_gateway.mock import MockBrokerAdapter

    # Only constructing a contract fixture is temporarily permitted; the actual
    # application operation is exercised with production fixture policy restored.
    monkeypatch.setenv("_QUANTLAB_TEST_FIXTURES", "1")
    broker = MockBrokerAdapter().snapshot()
    monkeypatch.delenv("_QUANTLAB_TEST_FIXTURES")
    monkeypatch.setattr("quantlab.app.reconciliation.last_snapshot", lambda: broker)
    assert run_payload()["status"] == "INTERNAL_STATE_UNAVAILABLE"
    path = tmp_path / "independent-internal-book.json"
    book = {
        "origin": "operator_internal_book",
        "independently_maintained": True,
        "snapshot": {
            "snapshot_id": "independent-event-ledger-1",
            "account_id_hash": broker.account.account_id_hash,
            "observed_at": broker.provenance.source_timestamp.isoformat(),
            "available_cash": 1.0,
            "available_margin": 1.0,
            "utilized_margin": 0.0,
        },
    }
    path.write_text(json.dumps(book), encoding="utf-8")
    imported = import_internal_books(path, repository_path=tmp_path / "agents.sqlite")
    result = run_payload(
        internal_snapshot_hash=imported["internal_snapshot_hash"],
        repository_path=tmp_path / "agents.sqlite",
    )
    # The deliberately old mock snapshot is stale under the production clock;
    # in no case may the independent book be reported as an exact match.
    assert result["status"] in {"MISMATCH", "RECONCILIATION_BREAK", "STALE"}
    assert result["internal_snapshot_id"] == "independent-event-ledger-1"
    assert result["live_trading"] is False


def test_observer_credentials_coexist_without_leaking_or_changing_environment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from quantlab.paper_oms.errors import PaperSafetyError
    from quantlab.paper_oms.safety import assert_paper_only

    path, ledger = tmp_path / "agents.sqlite", tmp_path / "ledger.jsonl"
    research, _ = _research(path)
    prepared = prepare_workflow(
        repository_path=path,
        ledger_path=ledger,
        research_result_hash=research,
        opening_cash=100000,
        reviewed=True,
        allow_unverified_liquidity=True,
    )
    monkeypatch.setenv("KITE_API_KEY", "observer-test-not-a-real-key")
    monkeypatch.setenv("KITE_API_SECRET", "observer-test-not-a-real-secret")
    for kind in ("paper_oms", "shadow", "twin"):
        result = execute_paper_workflow(
            _job(kind, prepared["workflow_id"]), repository_path=path, ledger_path=ledger
        )
        assert result["live_trading"] is False
        assert "observer-test-not-a-real-key" not in json.dumps(result)
    import os

    assert os.environ["KITE_API_KEY"] == "observer-test-not-a-real-key"
    # Scope is gone; the unbound legacy path still rejects credentials.
    with pytest.raises(PaperSafetyError, match="credentials"):
        assert_paper_only()


def test_live_credentials_still_rejected_with_sourced_workflow(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from quantlab.paper_oms.errors import PaperSafetyError

    path = tmp_path / "agents.sqlite"
    research, _ = _research(path)
    prepared = prepare_workflow(
        repository_path=path,
        research_result_hash=research,
        opening_cash=100000,
        reviewed=True,
        allow_unverified_liquidity=True,
    )
    monkeypatch.setenv("BROKER_PASSWORD", "contract-live-credential")
    with pytest.raises(PaperSafetyError, match="credentials"):
        execute_paper_workflow(
            _job("paper_oms", prepared["workflow_id"]),
            repository_path=path,
            ledger_path=tmp_path / "ledger.jsonl",
        )


def test_opening_account_state_is_part_of_paper_cache_identity(tmp_path: Path) -> None:
    from quantlab.app.paper_workflow import _run_paper
    from quantlab.paper_oms.models import CashLedger
    from quantlab.paper_oms.safety import sourced_simulation_scope

    path = tmp_path / "agents.sqlite"
    research, _ = _research(path)
    prepared = prepare_workflow(
        repository_path=path,
        research_result_hash=research,
        opening_cash=100000,
        reviewed=True,
        allow_unverified_liquidity=True,
    )
    repository = AgentRepository(path)
    try:
        inputs = load_workflow(repository, prepared["workflow_id"])
    finally:
        repository.close()
    with sourced_simulation_scope(inputs.content_hash):
        first = _run_paper(inputs)
        account = inputs.opening_account.model_copy(
            update={
                "cash": 200000.0,
                "available_cash": 200000.0,
                "equity": 200000.0,
                "ledger": CashLedger(opening_cash=200000, closing_cash=200000),
            }
        )
        changed = inputs.model_copy(update={"opening_account": account})
        second = _run_paper(changed)
        again = _run_paper(inputs)
    assert first.run.opening_account_hash != second.run.opening_account_hash
    assert first.run.oms_run_id != second.run.oms_run_id
    assert second.account.cash - first.account.cash == pytest.approx(100000)
    assert again.account.cash == first.account.cash


def test_shadow_cache_binds_changed_decision_and_target(tmp_path: Path) -> None:
    from quantlab.capital.decision import freeze_decision
    from quantlab.paper_oms.safety import sourced_simulation_scope
    from quantlab.shadow.models import ShadowRequest
    from quantlab.shadow.service import run_shadow_cycle

    path = tmp_path / "agents.sqlite"
    research, _ = _research(path)
    prepared = prepare_workflow(
        repository_path=path,
        research_result_hash=research,
        opening_cash=100000,
        reviewed=True,
        allow_unverified_liquidity=True,
    )
    repository = AgentRepository(path)
    try:
        inputs = load_workflow(repository, prepared["workflow_id"])
    finally:
        repository.close()
    snapshot = inputs.arrival.snapshot
    request = ShadowRequest(
        data_kind="REAL",
        decision_time=snapshot.as_of,
        available_time=snapshot.as_of,
        data_timestamp=snapshot.as_of,
        received_timestamp=snapshot.as_of,
        historical_replay=True,
        source_captured_at=snapshot.captured_at,
    )
    weights = {"NSE:AAA": 0.2, "NSE:BBB": 0.3}
    changed_decision = freeze_decision(
        inputs.decision.model_copy(
            update={
                "target_weights": weights,
                "gross_target": 0.5,
                "net_target": 0.5,
            }
        )
    )
    changed_target = inputs.target.model_copy(
        update={
            "decision_id": changed_decision.decision_id,
            "portfolio_hash": changed_decision.decision_hash,
            "weights": weights,
            "notional_targets": {name: value * 100000 for name, value in weights.items()},
            "cash_target": 50000,
        }
    )
    with sourced_simulation_scope(inputs.content_hash):
        first = run_shadow_cycle(
            request,
            decision=inputs.decision,
            target=inputs.target,
            account=inputs.opening_account,
            snapshot=snapshot,
        )
        second = run_shadow_cycle(
            request,
            decision=changed_decision,
            target=changed_target,
            account=inputs.opening_account,
            snapshot=snapshot,
        )
        again = run_shadow_cycle(
            request,
            decision=inputs.decision,
            target=inputs.target,
            account=inputs.opening_account,
            snapshot=snapshot,
        )
    assert first.cycle.cycle_id != second.cycle.cycle_id
    assert first.cycle.capital_decision_hash != second.cycle.capital_decision_hash
    assert first.paper_account.cash == again.paper_account.cash


def test_unpublished_shadow_cannot_seed_twin_match(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path, ledger = tmp_path / "agents.sqlite", tmp_path / "ledger.jsonl"
    research, _ = _research(path)
    prepared = prepare_workflow(
        repository_path=path,
        ledger_path=ledger,
        research_result_hash=research,
        opening_cash=100000,
        reviewed=True,
        allow_unverified_liquidity=True,
    )

    def fail(*_args: object, **_kwargs: object) -> None:
        raise OSError("contract shadow publication failure")

    monkeypatch.setattr("quantlab.app.paper_workflow._append_workflow_ledger", fail)
    with pytest.raises(OSError, match="shadow publication failure"):
        execute_paper_workflow(
            _job("shadow", prepared["workflow_id"]), repository_path=path, ledger_path=ledger
        )
    with pytest.raises(DataIntegrityError, match="PUBLISHED_SHADOW_RUN_REQUIRED"):
        execute_paper_workflow(
            _job("twin", prepared["workflow_id"]), repository_path=path, ledger_path=ledger
        )


def test_resealed_parent_swap_and_capital_swap_are_rejected(tmp_path: Path) -> None:
    path = tmp_path / "agents.sqlite"
    research_hash, _ = _research(path)
    prepared = prepare_workflow(
        repository_path=path,
        research_result_hash=research_hash,
        opening_cash=100000,
        reviewed=True,
        allow_unverified_liquidity=True,
    )
    other_capital = allocate_research_capital(
        repository_path=path,
        ledger_path=tmp_path / "ledger.jsonl",
        research_result_hash=research_hash,
        opening_cash=200000,
        allow_unverified_liquidity=True,
    )
    repository = AgentRepository(path)
    try:
        inputs = load_workflow(repository, prepared["workflow_id"])
        swapped = inputs.model_dump(mode="json")
        swapped["content_hash"] = ""
        swapped["research_result_hash"] = "f" * 64
        with pytest.raises(ValueError, match="DECISION_RESEARCH_PARENT_MISMATCH"):
            PaperWorkflowInputs.model_validate(swapped)
        swapped["research_result_hash"] = research_hash
        swapped["capital_allocation_hash"] = other_capital["result_hash"]
        bad_capital = repository.put(PaperWorkflowInputs.model_validate(swapped))
        with pytest.raises(DataIntegrityError, match="CAPITAL_WORKFLOW_BINDING_MISMATCH"):
            load_workflow(repository, bad_capital.content_hash)
    finally:
        repository.close()


@pytest.mark.parametrize("kind", ["capital", "prepare"])
def test_capital_and_preparation_honor_cancel_before_first_publication(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    kind: str,
) -> None:
    from quantlab.app import paper_workflow
    from quantlab.app.jobs import JobCancelledError
    from quantlab.app.paper_workflow import FrozenCapitalAllocation

    path, ledger = tmp_path / "agents.sqlite", tmp_path / "ledger.jsonl"
    research, _ = _research(path)
    job = _job(
        kind,
        "",
        research_result_hash=research,
        opening_cash=100000,
        reviewed=True,
        allow_unverified_liquidity=True,
    )
    calculate = paper_workflow._allocate_constructor_targets

    def cancel_after_compute(*args: Any, **kwargs: Any) -> Any:
        result = calculate(*args, **kwargs)
        assert job.request_cancel() is True
        return result

    monkeypatch.setattr(paper_workflow, "_allocate_constructor_targets", cancel_after_compute)
    with pytest.raises(JobCancelledError, match="before publication"):
        execute_paper_workflow(job, repository_path=path, ledger_path=ledger)
    repository = AgentRepository(path)
    try:
        assert repository.list(FrozenCapitalAllocation) == ()
        assert repository.list(PaperWorkflowInputs) == ()
    finally:
        repository.close()
    assert not ledger.exists()


def test_paper_cancel_after_compute_does_not_publish(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from quantlab.app import paper_workflow
    from quantlab.app.jobs import JobCancelledError
    from quantlab.app.paper_workflow import FrozenPaperWorkflowRun

    path, ledger = tmp_path / "agents.sqlite", tmp_path / "ledger.jsonl"
    research, _ = _research(path)
    prepared = prepare_workflow(
        repository_path=path,
        ledger_path=ledger,
        research_result_hash=research,
        opening_cash=100000,
        reviewed=True,
        allow_unverified_liquidity=True,
    )
    before = ledger.read_bytes()
    job = _job("paper_oms", prepared["workflow_id"])
    calculate = paper_workflow._run_paper

    def cancel_after_compute(*args: Any, **kwargs: Any) -> Any:
        assert kwargs["persist_result"] is False
        result = calculate(*args, **kwargs)
        assert job.request_cancel() is True
        return result

    monkeypatch.setattr(paper_workflow, "_run_paper", cancel_after_compute)
    with pytest.raises(JobCancelledError, match="before publication"):
        execute_paper_workflow(job, repository_path=path, ledger_path=ledger)
    repository = AgentRepository(path)
    try:
        assert repository.list(FrozenPaperWorkflowRun) == ()
    finally:
        repository.close()
    assert ledger.read_bytes() == before


def test_late_cancel_is_rejected_and_paper_job_completes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import time

    from quantlab.app.jobs import JobService
    from quantlab.app.paper_workflow import FrozenPaperWorkflowRun

    path, ledger = tmp_path / "agents.sqlite", tmp_path / "ledger.jsonl"
    research, _ = _research(path)
    prepared = prepare_workflow(
        repository_path=path,
        ledger_path=ledger,
        research_result_hash=research,
        opening_cash=100000,
        reviewed=True,
        allow_unverified_liquidity=True,
    )
    service = JobService(tmp_path / "jobs.sqlite", max_workers=1)
    active: dict[str, Job] = {}
    put = AgentRepository.put
    rejected: list[object] = []

    def late_cancel(repository: AgentRepository, artifact: Any) -> Any:
        if isinstance(artifact, FrozenPaperWorkflowRun):
            assert active["job"].publication_started
            rejected.append(service.cancel(active["job"].job_id))
        return put(repository, artifact)

    monkeypatch.setattr(AgentRepository, "put", late_cancel)

    def work(job: Job) -> dict[str, Any]:
        active["job"] = job
        return execute_paper_workflow(job, repository_path=path, ledger_path=ledger)

    try:
        job = service.submit(
            "paper_oms", work, {"kind": "paper_oms", "workflow_id": prepared["workflow_id"]}
        )
        deadline = time.monotonic() + 5
        while job.status in {JobStatus.QUEUED, JobStatus.RUNNING} and time.monotonic() < deadline:
            time.sleep(0.01)
        assert rejected == [False]
        assert job.status is JobStatus.COMPLETED
        assert job.result["result_hash"]
    finally:
        service.shutdown()
