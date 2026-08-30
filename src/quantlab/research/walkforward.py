"""Walk-forward window generation. Configurable; not a claim of optimal IS/OOS lengths."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from quantlab.research.splits import apply_embargo, purge_train_times


class WindowKind(StrEnum):
    ROLLING = "rolling"
    EXPANDING = "expanding"
    ANCHORED = "anchored"


class WalkForwardWindow(BaseModel):
    kind: WindowKind
    train_start: datetime
    train_end: datetime
    test_start: datetime
    test_end: datetime
    purged_train_end: datetime | None = None
    embargo_sessions: int = 0
    label_horizon_sessions: int = 1


class WalkForwardPlan(BaseModel):
    schema_version: str = "1"
    kind: WindowKind
    train_sessions: int
    test_sessions: int
    step_sessions: int
    embargo_sessions: int
    label_horizon_sessions: int
    windows: list[WalkForwardWindow] = Field(default_factory=list)


def generate_walk_forward(
    calendar: list[datetime],
    *,
    train_sessions: int,
    test_sessions: int,
    step_sessions: int,
    kind: WindowKind = WindowKind.EXPANDING,
    embargo_sessions: int = 0,
    label_horizon_sessions: int = 1,
) -> WalkForwardPlan:
    if min(train_sessions, test_sessions, step_sessions) < 1:
        raise ValueError("train, test, and step must be >= 1")
    n = len(calendar)
    windows: list[WalkForwardWindow] = []
    start_index = 0
    while True:
        if kind is WindowKind.ROLLING:
            train_start_i = start_index
            train_end_i = start_index + train_sessions - 1
        else:
            train_start_i = 0
            train_end_i = start_index + train_sessions - 1
        if train_end_i >= n:
            break
        train_end = calendar[train_end_i]
        test_start = apply_embargo(train_end, calendar, embargo_sessions)
        if test_start is None:
            break
        test_start_i = calendar.index(test_start)
        test_end_i = test_start_i + test_sessions - 1
        if test_end_i >= n:
            break
        train_times = calendar[train_start_i : train_end_i + 1]
        purged = purge_train_times(train_times, test_start, calendar, label_horizon_sessions)
        windows.append(
            WalkForwardWindow(
                kind=kind,
                train_start=calendar[train_start_i],
                train_end=train_end,
                test_start=test_start,
                test_end=calendar[test_end_i],
                purged_train_end=purged[-1] if purged else None,
                embargo_sessions=embargo_sessions,
                label_horizon_sessions=label_horizon_sessions,
            )
        )
        start_index += step_sessions
        if kind is not WindowKind.ROLLING and start_index + train_sessions >= n:
            break
    return WalkForwardPlan(
        kind=kind,
        train_sessions=train_sessions,
        test_sessions=test_sessions,
        step_sessions=step_sessions,
        embargo_sessions=embargo_sessions,
        label_horizon_sessions=label_horizon_sessions,
        windows=windows,
    )
