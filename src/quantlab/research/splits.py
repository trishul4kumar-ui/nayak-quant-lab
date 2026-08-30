"""Train / validation / test splits with purge and embargo."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel


class SplitRole(StrEnum):
    TRAIN = "train"
    VALIDATION = "validation"
    TEST = "test"


class TimeSplit(BaseModel):
    role: SplitRole
    start: datetime
    end: datetime


def apply_embargo(
    train_end: datetime,
    calendar: list[datetime],
    embargo_sessions: int,
) -> datetime | None:
    """First session strictly after train_end plus embargo_sessions."""
    if embargo_sessions < 0:
        raise ValueError("embargo_sessions cannot be negative")
    after = [t for t in calendar if t > train_end]
    if len(after) <= embargo_sessions:
        return None
    return after[embargo_sessions]


def purge_train_times(
    train: list[datetime],
    first_held_out: datetime,
    calendar: list[datetime],
    label_horizon_sessions: int,
) -> list[datetime]:
    """Drop training observations whose label horizon overlaps the held-out start."""
    if label_horizon_sessions < 0:
        raise ValueError("label_horizon_sessions cannot be negative")
    index = {t: i for i, t in enumerate(calendar)}
    if first_held_out not in index:
        return list(train)
    cutoff = index[first_held_out]
    kept: list[datetime] = []
    for t in train:
        i = index.get(t)
        if i is None:
            continue
        if i + label_horizon_sessions < cutoff:
            kept.append(t)
    return kept


def assert_temporally_ordered(windows: list[tuple[datetime, datetime]]) -> bool:
    previous_end: datetime | None = None
    for start, end in windows:
        if end < start:
            return False
        if previous_end is not None and start < previous_end:
            return False
        previous_end = end
    return True
