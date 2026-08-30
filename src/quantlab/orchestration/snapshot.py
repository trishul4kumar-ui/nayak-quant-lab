"""Pin the PIT dataset snapshot used by an experiment. Mismatch is a FAIL."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from quantlab.backtest.spec import config_hash
from quantlab.orchestration.errors import OrchestrationError


class DatasetSnapshot(BaseModel):
    dataset_id: str
    dataset_version: str
    snapshot_id: str
    checksum: str
    data_kind: str = "synthetic"
    n_days: int = 80
    universe_version: str = ""
    calendar_version: str = ""

    def identity_hash(self) -> str:
        return config_hash(self.model_dump(mode="json"))


def pin_from_frame(frame: Any) -> DatasetSnapshot:
    record = frame.record
    kind = record.data_kind
    data_kind = kind.value if hasattr(kind, "value") else str(kind)
    return DatasetSnapshot(
        dataset_id=str(record.dataset_id),
        dataset_version=str(record.version),
        snapshot_id=str(record.snapshot_id),
        checksum=str(record.checksum),
        data_kind=data_kind,
        universe_version=str(record.universe_version),
        calendar_version=str(record.calendar_version),
    )


def assert_same_snapshot(expected: DatasetSnapshot, actual: DatasetSnapshot) -> None:
    if expected.identity_hash() != actual.identity_hash():
        raise OrchestrationError("dataset snapshot mismatch; this is a new experiment lineage")
