"""Generated price paths here are deterministic software fixtures, NOT market evidence."""

from __future__ import annotations

import json
import math
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from quantlab.agents.contracts import AgentModelIdentity
from quantlab.agents.provider import ProviderHealth, StructuredRequest, UnavailableProvider
from quantlab.agents.repository import AgentRepository
from quantlab.app import strategy_research as engine
from quantlab.app.jobs import Job, JobStatus
from quantlab.app.market_backtest import (
    FrozenMarketHistory,
    HistoryBar,
    MarketBacktestParameters,
    calculate_market_backtest,
)
from quantlab.app.strategy_research import (
    FrozenStrategyBatch,
    FrozenStrategyFamily,
    FrozenStrategySelection,
    StrategyBatchParameters,
    execute_strategy_research,
    list_saved_strategies,
    list_strategy_batches,
    load_strategy_batch,
)
from quantlab.models.registry import ExperimentLedger
from quantlab.research.strategy_rules import (
    STRATEGY_NAMES,
    StrategyDefinition,
    StrategyRule,
    feature_values,
    matches,
    preset_strategy,
)


def history_fixture(n: int = 200) -> FrozenMarketHistory:
    start = datetime(2025, 1, 1, tzinfo=UTC)
    bars = []
    for i in range(n):
        close = 100 + i * 0.1 + 6 * math.sin(i / 4)
        bars.append(
            HistoryBar(
                time=start + timedelta(days=i),
                open=close - 0.1,
                high=close + 1,
                low=close - 1,
                close=close,
                volume=1000 + i,
            )
        )
    return FrozenMarketHistory(
        created_at=start + timedelta(days=300),
        captured_at=start + timedelta(days=300),
        instrument="NSE:INFY",
        interval="day",
        requested_days=366,
        candles=tuple(bars),
        excluded_forming_bars=0,
    )


class ProposalProvider:
    """Explicit test double: never labelled actual AI acceptance evidence."""

    def __init__(self, definitions: tuple[StrategyDefinition, ...] | None = None) -> None:
        self.definitions = definitions or (
            preset_strategy("momentum_v1", 5),
            preset_strategy("rsi_reversion_v1", 5),
        )
        self.requests: list[StructuredRequest] = []
        self.raw: str | None = None

    def generate_structured(self, request: StructuredRequest) -> str:
        self.requests.append(request)
        return (
            self.raw
            if self.raw is not None
            else json.dumps({"candidates": [d.model_dump(mode="json") for d in self.definitions]})
        )

    def continue_structured(self, request: StructuredRequest) -> str:
        return self.generate_structured(request)

    def health(self) -> ProviderHealth:
        return ProviderHealth(
            provider="test-double",
            model="fixture-only",
            configured=True,
            observed_status="NOT_TESTED",
        )

    def identity(self) -> AgentModelIdentity:
        return AgentModelIdentity(
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
            provider="test-double",
            model="fixture-only",
            version="v1",
        )


def make_job(history: FrozenMarketHistory, **changes: object) -> Job:
    params = StrategyBatchParameters.model_validate(
        {
            "instrument": history.instrument,
            "interval": history.interval,
            "days": history.requested_days,
            "history_hash": history.content_hash,
            **changes,
        }
    )
    return Job(
        "strategy-test",
        "ai_strategy_research",
        JobStatus.RUNNING,
        "now",
        parameters=params.model_dump(mode="json"),
    )


def execute(
    tmp_path: Path,
    provider: ProposalProvider | None = None,
    history: FrozenMarketHistory | None = None,
    job: Job | None = None,
):
    history = history or history_fixture()
    path = tmp_path / "agents.sqlite"
    repo = AgentRepository(path)
    repo.put(history)
    repo.close()
    return execute_strategy_research(
        job or make_job(history),
        path,
        tmp_path / "ledger.jsonl",
        tmp_path / "fabric",
        provider=provider or ProposalProvider(),
    )


@pytest.mark.parametrize("strategy", list(STRATEGY_NAMES))
def test_all_presets_are_causal_and_costed(strategy: str) -> None:
    history = history_fixture()
    params = MarketBacktestParameters(instrument=history.instrument, lookback=5, strategy=strategy)
    first = calculate_market_backtest(history, params)
    payload = history.model_dump(mode="json", exclude={"content_hash"})
    payload["candles"][-1].update(open=300, high=310, low=290, close=305)
    second = calculate_market_backtest(FrozenMarketHistory.model_validate(payload), params)
    assert first["equity_curve"][:-1] == second["equity_curve"][:-1]
    assert all(f["signal_bar"] < f["fill_bar"] and f["fee"] > 0 for f in first["fills"])
    assert first["execution_authority"] is False and first["gate_outcome"] == "NOT_TESTED"


def test_presets_do_not_alias_the_same_signal() -> None:
    h = history_fixture()
    paths = {
        tuple(
            calculate_market_backtest(
                h, MarketBacktestParameters(instrument=h.instrument, lookback=5, strategy=s)
            )["equity_curve"]
        )
        for s in STRATEGY_NAMES
    }
    assert len(paths) >= 4


def test_prior_channel_crossing_flat_rsi_and_missing_volume() -> None:
    bars = history_fixture().candles
    rule = StrategyRule(feature="breakout_high_gap", comparison="gt", period=5)
    assert feature_values(rule, bars)[5] == pytest.approx(
        bars[5].close / max(b.high for b in bars[:5]) - 1
    )
    crossing = StrategyRule(feature="return", comparison="cross_above", period=5)
    assert matches(crossing, [None, 0.1], 1) is False
    assert matches(crossing, [0.0, 0.1], 1) is True
    flat = tuple(
        HistoryBar(time=b.time, open=100, high=100, low=100, close=100, volume=None)
        for b in bars[:10]
    )
    assert feature_values(StrategyRule(feature="rsi", comparison="lt", period=5), flat)[-1] == 50
    with pytest.raises(ValueError, match="REAL_VOLUME_REQUIRED"):
        feature_values(StrategyRule(feature="volume_ratio", comparison="gt", period=5), flat)


def test_partial_allocation_and_close_triggered_stop_next_open() -> None:
    h = history_fixture()
    data = h.model_dump(mode="json", exclude={"content_hash"})
    for i, bar in enumerate(data["candles"]):
        close, opening = (97 if i == 5 else 100), (80 if i == 6 else 100)
        bar.update(open=opening, high=max(close, opening), low=min(close, opening), close=close)
    h = FrozenMarketHistory.model_validate(data)
    definition = StrategyDefinition(
        name="Gap stop fixture",
        hypothesis="Test close-triggered gaps.",
        entry=(StrategyRule(feature="return", comparison="ge", period=2, threshold=-1.0),),
        exit=(StrategyRule(feature="return", comparison="lt", period=2, threshold=-99.0),),
        allocation=0.5,
        stop_loss=0.02,
    )
    p = MarketBacktestParameters(
        instrument=h.instrument, lookback=5, strategy="rules_v1", definition=definition
    )
    r = calculate_market_backtest(h, p)
    assert r["fills"][0]["quantity"] * r["fills"][0]["price"] < 50000
    assert r["fills"][1]["price"] == pytest.approx(80 * 0.9995)
    assert r["fills"][1]["reason"] == "close_triggered_risk_exit"
    assert 0 <= r["metrics"]["mean_exposure"] <= 1


@pytest.mark.parametrize(
    "bad",
    [
        {"feature": "python"},
        {"period": True},
        {"period": 61},
        {"threshold": True},
        {"code": "print(1)"},
        {"feature": "rsi", "threshold": -1.0},
        {"feature": "sma_cross_gap", "period": 40, "slow_period": 5},
    ],
)
def test_model_rules_are_bounded_data_only(bad: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        StrategyRule.model_validate({"feature": "return", "comparison": "gt", **bad})


def test_automatic_batch_only_winner_holdout_and_exact_saved_report(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = engine.calculate_market_backtest
    calls = []

    def observed(history, params, **kwargs):
        calls.append(
            (params.definition.identity_hash(), kwargs["start_index"], kwargs["end_index"])
        )
        if kwargs["end_index"] == len(history.candles):
            repo = AgentRepository(tmp_path / "agents.sqlite")
            try:
                assert repo.list(FrozenStrategySelection)  # Freeze precedes holdout computation.
                assert any(e.event == "STRATEGY_SELECTION_FROZEN" for e in repo.audit_events())
            finally:
                repo.close()
        return original(history, params, **kwargs)

    monkeypatch.setattr(engine, "calculate_market_backtest", observed)
    provider = ProposalProvider()
    result = execute(tmp_path, provider)
    assert len(provider.requests) == 1
    assert len(result["attempts"]) == 3 and result["holdout"] is not None
    holdout_calls = [c for c in calls if c[2] == len(history_fixture().candles)]
    assert len(holdout_calls) == 1
    assert holdout_calls[0][0] == result["winner_strategy_hash"]
    training = json.loads(dict(provider.requests[0].sections)["training_only"])
    assert training["end"] < result["context"]["validation_start"]
    assert "holdout" not in training and "prices" not in training
    schema = json.loads(provider.requests[0].schema_json)
    assert schema["properties"]["candidates"]["maxItems"] == 4
    path = tmp_path / "agents.sqlite"
    assert load_strategy_batch(path, result["result_hash"]).envelope() == result
    assert len(list_saved_strategies(path)) == 2  # Baseline is not labelled AI authored.
    row = ExperimentLedger(tmp_path / "ledger.jsonl").get(result["run_id"])
    assert row is not None and row.gate_outcome == "NOT_TESTED"
    assert result["data_kind"] == "REAL" and result["broker_write_enabled"] is False
    assert "Long/cash only" in result["winner_rule_description"]
    assert any("unverified model text" in w for w in result["warnings"])


def test_family_is_frozen_before_first_candidate_and_reopens(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = engine.calculate_market_backtest
    checked = False

    def inspect_family(*args, **kwargs):
        nonlocal checked
        if not checked:
            repository = AgentRepository(tmp_path / "agents.sqlite")
            try:
                families = repository.list(FrozenStrategyFamily)
                assert len(families) == 1
                events = repository.audit_events(families[0].batch_id)
                assert any(e.event == "STRATEGY_FAMILY_FROZEN" for e in events)
                assert not any(e.event == "STRATEGY_CANDIDATE_ATTEMPT" for e in events)
                assert len(families[0].candidates) == 3
                checked = True
            finally:
                repository.close()
        return original(*args, **kwargs)

    monkeypatch.setattr(engine, "calculate_market_backtest", inspect_family)
    result = execute(tmp_path)
    assert checked
    reopened = load_strategy_batch(tmp_path / "agents.sqlite", result["result_hash"])
    assert reopened.envelope()["context"]["family_hash"] == result["context"]["family_hash"]


def test_tampered_family_fails_on_reopen(tmp_path: Path) -> None:
    result = execute(tmp_path)
    path = tmp_path / "agents.sqlite"
    with sqlite3.connect(path) as connection:
        row = connection.execute(
            "SELECT payload_json FROM control_plane_records "
            "WHERE namespace = ? AND identity = ?",
            ("agent_artifacts", result["context"]["family_hash"]),
        ).fetchone()
        assert row is not None
        payload = json.loads(row[0])
        payload["artifact"]["candidates"][0][1] = "tampered"
        connection.execute(
            "UPDATE control_plane_records SET payload_json = ? "
            "WHERE namespace = ? AND identity = ?",
            (json.dumps(payload), "agent_artifacts", result["context"]["family_hash"]),
        )
    with pytest.raises(ValueError, match="artifact content hash mismatch"):
        load_strategy_batch(path, result["result_hash"])


@pytest.mark.parametrize("change", ["score", "remove_family"])
def test_resealed_report_cannot_change_selection_evidence(tmp_path: Path, change: str) -> None:
    result = execute(tmp_path)
    path = tmp_path / "agents.sqlite"
    original = load_strategy_batch(path, result["result_hash"])
    report = json.loads(original.report_json)
    if change == "score":
        selected_attempt = next(
            a for a in report["attempts"] if a["strategy_hash"] == report["winner_strategy_hash"]
        )
        selected_attempt["selection_score"] += 10.0
    else:
        del report["context"]["family_hash"]
    content = original.model_dump(mode="json", exclude={"content_hash"})
    content["report_json"] = json.dumps(report, sort_keys=True, allow_nan=False)
    resealed = FrozenStrategyBatch.model_validate(content)
    repository = AgentRepository(path)
    try:
        repository.put(resealed)
        repository.audit(
            "STRATEGY_BATCH_COMPLETED",
            run_id=resealed.batch_id,
            now=datetime.now(UTC),
            artifact_hash=resealed.content_hash,
        )
    finally:
        repository.close()
    with pytest.raises(
        ValueError, match="STRATEGY_BATCH_(SELECTION_SCORE|FAMILY_BINDING)_MISMATCH"
    ):
        load_strategy_batch(path, resealed.content_hash)


def test_holdout_prices_cannot_change_model_input_or_winner(tmp_path: Path) -> None:
    provider = ProposalProvider()
    first = execute(tmp_path, provider)
    data = history_fixture().model_dump(mode="json", exclude={"content_hash"})
    for b in data["candles"][-30:]:
        for field in ("open", "high", "low", "close"):
            b[field] *= 2
    second = execute(tmp_path, provider, FrozenMarketHistory.model_validate(data))
    assert provider.requests[0].sections == provider.requests[1].sections
    assert first["winner_strategy_hash"] == second["winner_strategy_hash"]
    assert [a.get("selection_score") for a in first["attempts"]] == [
        a.get("selection_score") for a in second["attempts"]
    ]
    assert second["holdout_reused"] is True  # New capture hash does not hide overlapping dates.


def test_duplicate_and_untraded_candidates_are_reported_not_faked(tmp_path: Path) -> None:
    base = preset_strategy("close_sma_next_open_v1", 20).model_dump(mode="json")
    base.update(name="Disguised baseline", hypothesis="Different text but identical economics.")
    base["entry"][0]["slow_period"] = 31  # Unused fields cannot disguise duplicate rules.
    base["exit"][0]["slow_period"] = 32
    silent = preset_strategy("momentum_v1", 5).model_dump(mode="json")
    silent["entry"][0]["threshold"] = 99.0
    result = execute(
        tmp_path,
        ProposalProvider(tuple(StrategyDefinition.model_validate(d) for d in (base, silent))),
    )
    assert result["winner_strategy_hash"] is None and result["holdout"] is None
    assert result["attempts"][1]["reason"] == "DUPLICATE_STRATEGY_RULES"
    assert result["attempts"][2]["reason"] == "INSUFFICIENT_TRADED_SEGMENTS"
    assert "abstained" in result["summary"]


def test_invalid_provider_response_never_becomes_a_host_authored_ai_result(tmp_path: Path) -> None:
    provider = ProposalProvider()
    provider.raw = '{"candidates": [{"code": "import os"}]}'
    with pytest.raises(Exception, match="INVALID_STRUCTURED_OUTPUT"):
        execute(tmp_path, provider)
    assert len(provider.requests) == 2  # Single bounded schema retry, no fallback provider.
    assert list_strategy_batches(tmp_path / "agents.sqlite") == ()
    assert not (tmp_path / "ledger.jsonl").exists()


def test_budget_exhaustion_publishes_truthful_partial_report(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clock = [0.0]
    monkeypatch.setattr(engine, "time", SimpleNamespace(monotonic=lambda: clock[0]))
    original = engine.calculate_market_backtest

    def exhaust(*args, **kwargs):
        result = original(*args, **kwargs)
        clock[0] = 9999.0
        return result

    monkeypatch.setattr(engine, "calculate_market_backtest", exhaust)
    result = execute(tmp_path)
    assert result["batch_status"] == "BUDGET_EXHAUSTED"
    assert result["holdout"] is None and "partial report" in result["summary"]
    assert all(a["status"] == "rejected" for a in result["attempts"])


def test_cancel_after_selection_never_publishes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    h = history_fixture()
    job = make_job(h)
    original = AgentRepository.audit

    def cancel_on_selection(self, event, **kwargs):
        row = original(self, event, **kwargs)
        if event == "STRATEGY_SELECTION_FROZEN":
            job.cancel_event.set()
        return row

    monkeypatch.setattr(AgentRepository, "audit", cancel_on_selection)
    with pytest.raises(Exception, match="cancelled"):
        execute(tmp_path, history=h, job=job)
    assert list_strategy_batches(tmp_path / "agents.sqlite") == ()
    assert list_saved_strategies(tmp_path / "agents.sqlite") == ()


def test_failed_publication_and_wrong_context_excluded(tmp_path: Path, monkeypatch):
    with monkeypatch.context() as patch:

        def fail(*args, **kwargs):
            raise OSError("LEDGER_FAILED")

        patch.setattr(ExperimentLedger, "append", fail)
        with pytest.raises(OSError, match="LEDGER_FAILED"):
            execute(tmp_path)
        assert list_strategy_batches(tmp_path / "agents.sqlite") == ()
    result = execute(tmp_path)
    path = tmp_path / "agents.sqlite"
    original = load_strategy_batch(path, result["result_hash"])
    data = original.model_dump(mode="json", exclude={"content_hash"})
    data["parameters"]["instrument"] = "NSE:TCS"
    wrong = FrozenStrategyBatch.model_validate(data)
    repo = AgentRepository(path)
    try:
        repo.put(wrong)
        repo.audit(
            "STRATEGY_BATCH_COMPLETED",
            run_id=wrong.batch_id,
            now=datetime.now(UTC),
            artifact_hash=wrong.content_hash,
        )
    finally:
        repo.close()
    with pytest.raises(ValueError, match="CONTEXT_BINDING"):
        load_strategy_batch(path, wrong.content_hash)


def test_unconfigured_model_and_short_history_fail_explicitly(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="MODEL_NOT_CONFIGURED"):
        execute_strategy_research(
            make_job(history_fixture()),
            tmp_path / "a.sqlite",
            tmp_path / "ledger.jsonl",
            tmp_path / "fabric",
            provider=UnavailableProvider(),
        )
    with pytest.raises(ValueError, match="SPLITS_TOO_SHORT"):
        execute(tmp_path, history=history_fixture(60))
