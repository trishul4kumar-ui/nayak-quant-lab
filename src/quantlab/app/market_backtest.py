"""Frozen broker-history research, with close signals and next-bar open fills.

These are bounded single-instrument price rules, not an order or paper OMS client.
Broker history is not certified point-in-time/corporate-action-adjusted evidence.
"""

from __future__ import annotations

import json
import math
import statistics
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

from quantlab import __version__
from quantlab.agents.hashing import Artifact, digest
from quantlab.agents.repository import AgentRepository
from quantlab.app.jobs import Job
from quantlab.domain.models import ExperimentRun, ExperimentStatus
from quantlab.models.registry import ExperimentLedger
from quantlab.realtime_data.candles import INTERVALS, CandleSeries, ChartRequest, KiteCandleClient
from quantlab.realtime_data.service import _assert_safety
from quantlab.research.strategy_rules import (
    StrategyDefinition,
    StrategyId,
    preset_strategy,
    strategy_signals,
)

MarketInterval = Literal[
    "minute", "3minute", "5minute", "10minute", "15minute", "30minute", "60minute", "day"
]


class MarketBacktestParameters(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)
    instrument: str = Field(pattern=r"^(?:NSE|BSE):[A-Z0-9_.-]+$", max_length=80)
    interval: MarketInterval = "day"
    days: int = Field(default=366, ge=1, le=366, strict=True)
    lookback: int = Field(default=20, ge=5, le=60, strict=True)
    cost_bps: float = Field(default=10.0, ge=0.1, le=100, strict=True)
    slippage_bps: float = Field(default=5.0, ge=0, le=100, strict=True)
    strategy: StrategyId = "close_sma_next_open_v1"
    definition: StrategyDefinition | None = None
    data_kind: Literal["REAL"] = "REAL"

    @model_validator(mode="after")
    def bounded_range(self) -> MarketBacktestParameters:
        if self.interval != "day" and self.days > 31:
            raise ValueError("INTRADAY_HISTORY_BOUND_EXCEEDED")
        if (self.strategy == "rules_v1") != (self.definition is not None):
            raise ValueError("CUSTOM_STRATEGY_REQUIRES_EXACT_DEFINITION")
        return self

    def resolved_strategy(self) -> StrategyDefinition:
        return self.definition or preset_strategy(self.strategy, self.lookback)

    def request(self) -> ChartRequest:
        return ChartRequest(self.instrument, self.interval, self.days)


class HistoryBar(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)
    time: AwareDatetime
    open: float = Field(gt=0)
    high: float = Field(gt=0)
    low: float = Field(gt=0)
    close: float = Field(gt=0)
    volume: float | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def valid_ohlc(self) -> HistoryBar:
        if not self.low <= min(self.open, self.close) <= max(self.open, self.close) <= self.high:
            raise ValueError("INVALID_OHLC")
        return self


class FrozenMarketHistory(Artifact):
    instrument: str
    interval: MarketInterval
    requested_days: int
    captured_at: AwareDatetime
    source: Literal["kite-historical-v3"] = "kite-historical-v3"
    data_kind: Literal["REAL"] = "REAL"
    candles: tuple[HistoryBar, ...] = Field(min_length=1, max_length=12000)
    excluded_forming_bars: int = Field(ge=0)
    price_adjustment: Literal["BROKER_PROVIDED_UNVERIFIED"] = "BROKER_PROVIDED_UNVERIFIED"
    execution_authority: Literal[False] = False

    @model_validator(mode="after")
    def chronology(self) -> FrozenMarketHistory:
        duration = timedelta(seconds=INTERVALS[self.interval])
        if any(bar.time + duration > self.captured_at for bar in self.candles):
            raise ValueError("INCOMPLETE_HISTORY_BAR")
        if any(b.time <= a.time for a, b in zip(self.candles, self.candles[1:], strict=False)):
            raise ValueError("HISTORY_CHRONOLOGY_INVALID")
        if any(
            b.time - a.time < duration for a, b in zip(self.candles, self.candles[1:], strict=False)
        ):
            raise ValueError("OVERLAPPING_HISTORY_BARS")
        return self


class FrozenMarketBacktest(Artifact):
    history_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    parameters: MarketBacktestParameters
    result: dict[str, Any]
    execution_authority: Literal[False] = False


def verify_frozen_market_result(
    repository: AgentRepository, result: dict[str, Any], parameters: MarketBacktestParameters
) -> FrozenMarketHistory:
    report = repository.get(str(result.get("result_hash", "")), FrozenMarketBacktest)
    if report.parameters != parameters or report.result != {
        key: value for key, value in result.items() if key != "result_hash"
    }:
        raise ValueError("REAL_RESULT_ARTIFACT_BINDING_MISMATCH")
    history = repository.get(report.history_hash, FrozenMarketHistory)
    if (
        result.get("data_kind") != "REAL"
        or result.get("source") != history.source
        or result.get("history_hash") != history.content_hash
        or (history.instrument, history.interval, history.requested_days)
        != (parameters.instrument, parameters.interval, parameters.days)
    ):
        raise ValueError("REAL_RESULT_HISTORY_BINDING_MISMATCH")
    return history


def freeze_history(
    series: CandleSeries, parameters: MarketBacktestParameters, *, now: datetime
) -> FrozenMarketHistory:
    if series.source != "kite-historical-v3" or series.request != parameters.request():
        raise ValueError("REAL_HISTORY_BINDING_MISMATCH")
    if series.fetched_at.tzinfo is None or now.tzinfo is None:
        raise ValueError("HISTORY_CLOCK_REQUIRED")
    age = (now - series.fetched_at).total_seconds()
    if not 0 <= age <= 120:
        raise ValueError("HISTORY_CAPTURE_STALE_OR_FUTURE")
    # Daily bars are conservatively excluded until the following midnight;
    # quote polling is never used to manufacture missing candles.
    closed = tuple(bar for bar in series.candles if not series.is_forming(bar))
    if len(closed) < parameters.lookback + 3:
        raise ValueError("INSUFFICIENT_CLOSED_HISTORY_BARS")
    earliest = series.fetched_at - timedelta(days=parameters.days + 1)
    if any(bar.time < earliest or bar.time > series.fetched_at for bar in series.candles):
        raise ValueError("HISTORY_OUTSIDE_REQUESTED_RANGE")
    return FrozenMarketHistory(
        created_at=now,
        instrument=parameters.instrument,
        interval=parameters.interval,
        requested_days=parameters.days,
        captured_at=series.fetched_at,
        candles=tuple(
            HistoryBar(
                time=bar.time,
                open=bar.open,
                high=bar.high,
                low=bar.low,
                close=bar.close,
                volume=bar.volume,
            )
            for bar in closed
        ),
        excluded_forming_bars=len(series.candles) - len(closed),
    )


def calculate_market_backtest(
    history: FrozenMarketHistory,
    parameters: MarketBacktestParameters,
    *,
    cancelled: Callable[[], bool] = lambda: False,
    start_index: int | None = None,
    end_index: int | None = None,
) -> dict[str, Any]:
    history.verified()
    if (history.instrument, history.interval, history.requested_days) != (
        parameters.instrument,
        parameters.interval,
        parameters.days,
    ) or len(history.candles) < parameters.lookback + 3:
        raise ValueError("BACKTEST_HISTORY_BINDING_MISMATCH")
    definition = parameters.resolved_strategy()
    first = (
        start_index if start_index is not None else max(parameters.lookback, definition.warmup())
    )
    stop = end_index if end_index is not None else len(history.candles)
    if not definition.warmup() <= first < stop <= len(history.candles) or stop - first < 2:
        raise ValueError("INSUFFICIENT_STRATEGY_OR_SEGMENT_HISTORY")
    bars = history.candles[:stop]
    # Only the causal warm-up prefix and requested evaluation segment are needed.
    # Old unrelated history cannot defeat a bounded batch's bar/compute budget.
    feature_start = max(0, first - definition.warmup() - 1)
    entries, exits = strategy_signals(definition, bars[feature_start:], cancelled)
    initial = cash = 100000.0
    units = 0.0
    entry_price, entry_index = 0.0, 0
    fee_rate, slip = parameters.cost_bps / 10000, parameters.slippage_bps / 10000
    curve, dates, exposures, fills = (
        [initial],
        [history.candles[first - 1].time.isoformat()],
        [],
        [],
    )
    cost_paid = 0.0
    for index in range(first, stop):
        if cancelled():
            raise ValueError("cancelled")
        previous, bar = bars[index - 1], bars[index]
        return_from_entry = previous.close / entry_price - 1 if entry_price > 0 else 0.0
        risk_exit = units > 0 and (
            (definition.stop_loss > 0 and return_from_entry <= -definition.stop_loss)
            or (definition.take_profit > 0 and return_from_entry >= definition.take_profit)
            or (
                definition.max_holding_bars > 0
                and index - entry_index >= definition.max_holding_bars
            )
        )
        signal_index = index - 1 - feature_start
        if entries[signal_index] and units == 0:
            price = bar.open * (1 + slip)
            budget = cash * definition.allocation
            units = budget / (price * (1 + fee_rate))
            fee = units * price * fee_rate
            cost_paid += fee + units * (price - bar.open)
            cash -= units * price + fee
            entry_price, entry_index = price, index
            fills.append(
                {
                    "side": "BUY",
                    "signal_bar": previous.time.isoformat(),
                    "fill_bar": bar.time.isoformat(),
                    "price": price,
                    "fee": fee,
                    "quantity": units,
                    "simulated": True,
                }
            )
        elif (exits[signal_index] or risk_exit) and units > 0:
            price = bar.open * (1 - slip)
            fee = units * price * fee_rate
            cost_paid += fee + units * (bar.open - price)
            cash += units * price - fee
            fills.append(
                {
                    "side": "SELL",
                    "signal_bar": previous.time.isoformat(),
                    "fill_bar": bar.time.isoformat(),
                    "price": price,
                    "fee": fee,
                    "quantity": units,
                    "simulated": True,
                    "reason": "close_triggered_risk_exit" if risk_exit else "exit_rule",
                }
            )
            units = 0.0
        equity = cash + units * bar.close
        if not math.isfinite(equity) or equity <= 0:
            raise ValueError("NONFINITE_OR_NONPOSITIVE_BACKTEST_EQUITY")
        curve.append(equity)
        dates.append(bar.time.isoformat())
        exposures.append(units * bar.close / equity if units > 0 else 0.0)
    returns = [right / left - 1 for left, right in zip(curve, curve[1:], strict=False)]
    periods = (
        252.0 if parameters.interval == "day" else 252 * 375 * 60 / INTERVALS[parameters.interval]
    )
    deviation = statistics.pstdev(returns)
    peak, drawdown = initial, 0.0
    for equity in curve:
        peak = max(peak, equity)
        drawdown = min(drawdown, equity / peak - 1)
    benchmark_units = initial / (bars[first].open * (1 + slip) * (1 + fee_rate))
    benchmark = [initial] + [benchmark_units * bar.close for bar in bars[first:stop]]
    metrics = {
        "total_return": curve[-1] / initial - 1,
        "max_drawdown": drawdown,
        "sharpe": statistics.mean(returns) / deviation * math.sqrt(periods) if deviation else 0.0,
        "volatility": deviation * math.sqrt(periods),
        "cost_drag": cost_paid / initial,
        "n_trades": float(len(fills)),
        "mean_exposure": statistics.mean(exposures),
        "initial_equity": initial,
        "ending_equity": curve[-1],
        "benchmark_total_return": benchmark[-1] / initial - 1,
    }
    if any(not math.isfinite(value) for value in metrics.values()):
        raise ValueError("NONFINITE_BACKTEST_METRIC")
    identity = digest(
        {
            "parameters": parameters.model_dump(mode="json"),
            "history_hash": history.content_hash,
            "fill_policy": "next_bar_open",
            "strategy_hash": definition.identity_hash(),
            "evaluation_slice": [first, stop],
        }
    )
    return {
        "data_kind": "REAL",
        "source": history.source,
        "instrument": history.instrument,
        "interval": history.interval,
        "strategy": parameters.strategy,
        "strategy_definition": definition.model_dump(mode="json"),
        "strategy_hash": definition.identity_hash(),
        "evaluation_slice": [first, stop],
        "history_hash": history.content_hash,
        "dataset_id": history.content_hash,
        "config_hash": identity,
        "equity_curve": curve,
        "benchmark_curve": benchmark,
        "dates": dates,
        "metrics": metrics,
        "fills": fills,
        "live_trading": False,
        "execution_authority": False,
        "closed_bar_count": len(history.candles),
        "history_captured_at": history.captured_at.isoformat(),
        "excluded_forming_bars": history.excluded_forming_bars,
        "integrity": {
            "source": history.source,
            "data_kind": "REAL",
            "fill_policy": "next_bar_open",
            "same_bar_fills": "FORBIDDEN",
            "missing_bars": "NOT_FILLED",
            "corporate_actions": "NOT_TESTED",
            "point_in_time_revisions": "NOT_TESTED",
            "signal": "completed_bar_rules_with_next_available_open_fills",
            "strategy_name": definition.name,
            "strategy_hash": definition.identity_hash(),
            "risk_exits": "CLOSE_TRIGGERED_NEXT_OPEN_NOT_INTRABAR_STOPS",
            "annualization": "252 sessions; intraday assumes 375 minutes per session",
            "ending_position": "MARKED_AT_CLOSE_WITHOUT_FORCED_LIQUIDATION",
            "first_closed_bar": bars[0].time.isoformat(),
            "last_closed_bar": bars[-1].time.isoformat(),
            "timestamp_meaning": "BROKER_BAR_START_UTC",
        },
        "gate_outcome": "NOT_TESTED",
        "conclusion": "Real broker-history strategy research; simulated fills only. "
        "Corporate actions, historic revisions and out-of-sample robustness are "
        "not verified. Not live/paper readiness or proof of profitability.",
    }


def execute_market_backtest(
    job: Job,
    ledger_path: Path,
    artifacts_dir: Path,
    repository_path: Path,
    *,
    fetch: Callable[[ChartRequest], CandleSeries] | None = None,
    fabric_root: Path | None = None,
) -> dict[str, Any]:
    _assert_safety()
    parameters = MarketBacktestParameters.model_validate(job.parameters)
    if job.cancel_event.is_set():
        raise ValueError("cancelled")
    job.progress = 0.1
    series = (fetch or KiteCandleClient().fetch)(parameters.request())
    history = freeze_history(series, parameters, now=datetime.now(UTC))
    if job.cancel_event.is_set():
        raise ValueError("cancelled")
    _assert_safety()
    repository = AgentRepository(repository_path)
    try:
        repository.put(history)
    finally:
        repository.close()
    if fabric_root is not None:
        from quantlab.app.real_history import register_history

        register_history(history, fabric_root)
    job.progress = 0.4
    result = calculate_market_backtest(history, parameters, cancelled=job.cancel_event.is_set)
    _assert_safety()
    if job.cancel_event.is_set():
        raise ValueError("cancelled")
    experiment_id = "market-" + uuid4().hex
    run = ExperimentRun(
        id=experiment_id,
        name=parameters.strategy + " · " + parameters.instrument,
        hypothesis=parameters.resolved_strategy().hypothesis,
        status=ExperimentStatus.COMPLETED,
        dataset_version=history.content_hash,
        dataset_id=history.content_hash,
        snapshot_id=history.content_hash,
        universe=[parameters.instrument],
        data_kind="real",
        price_adjustment_method="broker_provided_unverified",
        corporate_action_policy="NOT_TESTED",
        hyperparameters={
            **parameters.model_dump(mode="json", exclude={"definition"}),
            "definition_json": parameters.resolved_strategy().model_dump_json(),
        },
        transaction_cost_bps=parameters.cost_bps,
        slippage_model="proportional_bps",
        lineage={"history_hash": history.content_hash, "source": history.source},
        metrics=result["metrics"],
        integrity=result["integrity"],
        config_hash=result["config_hash"],
        application_version=__version__,
        conclusion=result["conclusion"],
        gate_outcome="NOT_TESTED",
        validation_protocol="UNVALIDATED_REAL_HISTORY_BASELINE",
    )
    job.begin_publication()
    directory = artifacts_dir / experiment_id
    directory.mkdir(parents=True, exist_ok=False)
    (directory / "equity.json").write_text(
        json.dumps({"equity": result["equity_curve"]}), encoding="utf-8"
    )
    output = {**result, "experiment_id": experiment_id, "status": run.status.value}
    repository = AgentRepository(repository_path)
    try:
        report = repository.put(
            FrozenMarketBacktest(
                created_at=datetime.now(UTC),
                history_hash=history.content_hash,
                parameters=parameters,
                result=output,
            )
        )
    finally:
        repository.close()
    _assert_safety()
    (directory / "market_backtest.json").write_text(
        json.dumps({**output, "result_hash": report.content_hash}), encoding="utf-8"
    )
    ExperimentLedger(ledger_path).append(run)
    job.progress = 0.95
    return {**output, "result_hash": report.content_hash}
