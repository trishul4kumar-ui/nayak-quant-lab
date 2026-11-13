"""Reusable frozen broker-history capture. Acquisition is not PIT certification."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from quantlab.agents.repository import AgentRepository
from quantlab.app.jobs import Job
from quantlab.app.market_backtest import (
    FrozenMarketHistory,
    MarketBacktestParameters,
    freeze_history,
)
from quantlab.data.fabric.catalog import DatasetCatalog, DatasetRecord
from quantlab.data.fabric.layout import FabricLayout
from quantlab.data.fabric.types import DataKind, DatasetState
from quantlab.realtime_data.candles import KiteCandleClient
from quantlab.realtime_data.service import _assert_safety


def register_history(history: FrozenMarketHistory, fabric_root: Path) -> DatasetRecord:
    history.verified()
    record = DatasetRecord(
        dataset_id="kite-" + history.instrument.replace(":", "-") + "-" + history.interval,
        version=history.content_hash,
        state=DatasetState.NOT_READY,
        data_kind=DataKind.REAL,
        source=history.source,
        checksum=history.content_hash,
        schema_name="frozen_kite_candles_v1",
        snapshot_id=history.content_hash,
        coverage=f"rows={len(history.candles)} instruments=1",
        price_adjustment_method="broker_provided_unverified",
        corporate_action_policy="NOT_TESTED",
        notes="REAL broker capture; historical availability/revisions, corporate actions "
        "and membership are NOT_TESTED. Not a certified PIT dataset.",
        extra={
            "history_hash": history.content_hash,
            "captured_at": history.captured_at.isoformat(),
            "first_bar": history.candles[0].time.isoformat(),
            "last_bar": history.candles[-1].time.isoformat(),
            "historical_availability_verified": "false",
            "exploratory_ready": "true",
            "closed_bar_count": str(len(history.candles)),
            "instrument_count": "1",
            "interval": history.interval,
            "artifact_store": "agent_desk.sqlite",
        },
    )
    with DatasetCatalog(FabricLayout(fabric_root)) as catalog:
        catalog.upsert(record)
    return record


def execute_history_capture(job: Job, repository_path: Path, fabric_root: Path) -> dict[str, Any]:
    _assert_safety()
    parameters = MarketBacktestParameters.model_validate(job.parameters)
    if job.cancel_event.is_set():
        raise ValueError("cancelled")
    job.progress = 0.1
    history = freeze_history(
        KiteCandleClient().fetch(parameters.request()), parameters, now=datetime.now(UTC)
    )
    _assert_safety()
    if job.cancel_event.is_set():
        raise ValueError("cancelled")
    job.begin_publication()
    repository = AgentRepository(repository_path)
    try:
        repository.put(history)
    finally:
        repository.close()
    record = register_history(history, fabric_root)
    return {
        "data_kind": "REAL",
        "source": history.source,
        "instrument": history.instrument,
        "interval": history.interval,
        "history_hash": history.content_hash,
        "closed_bar_count": len(history.candles),
        "captured_at": history.captured_at.isoformat(),
        "dataset_id": record.dataset_id,
        "research_ready": False,
        "exploratory_ready": True,
        "input_tier": "EXPLORATORY",
        "historical_availability_verified": False,
        "live_trading": False,
        "execution_authority": False,
    }
