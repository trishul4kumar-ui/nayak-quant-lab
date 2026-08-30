"""Immutable research snapshots bind dataset/master/calendar/CA/universe versions."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field

from quantlab.backtest.spec import config_hash


class ResearchDataSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)

    snapshot_id: str
    dataset_id: str
    dataset_version: str
    dataset_checksum: str
    security_master_version: str
    calendar_version: str
    corporate_action_version: str
    universe_version: str
    schema_version: str = "ohlcv-v1"
    created_at: datetime = Field(default_factory=lambda: datetime(2024, 1, 15, tzinfo=UTC))
    snapshot_hash: str = ""
    note: str = "Changing any dependency creates a new snapshot. Old snapshots stay immutable."


def freeze_snapshot(**kwargs: str) -> ResearchDataSnapshot:
    payload: dict[str, object] = {key: value for key, value in kwargs.items()}
    digest = config_hash(payload)
    snap = ResearchDataSnapshot(
        snapshot_id=f"SNAP-{digest[:12]}",
        dataset_id=kwargs.get("dataset_id", ""),
        dataset_version=kwargs.get("dataset_version", ""),
        dataset_checksum=kwargs.get("dataset_checksum", ""),
        security_master_version=kwargs.get("security_master_version", ""),
        calendar_version=kwargs.get("calendar_version", ""),
        corporate_action_version=kwargs.get("corporate_action_version", ""),
        universe_version=kwargs.get("universe_version", ""),
        schema_version=kwargs.get("schema_version", "ohlcv-v1"),
    )
    return snap.model_copy(update={"snapshot_hash": digest})
