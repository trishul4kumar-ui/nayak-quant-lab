"""Explicit bounded multi-instrument GET-only capture for research workspaces."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from quantlab.app.jobs import Job, JobStatus
from quantlab.app.market_backtest import MarketBacktestParameters
from quantlab.app.real_history import execute_history_capture


class HistoryCaptureBatch(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    instruments: tuple[str, ...] = Field(min_length=1, max_length=64)
    interval: str = "day"
    days: int = Field(default=366, ge=1, le=366, strict=True)

    @model_validator(mode="after")
    def validate_requests(self) -> HistoryCaptureBatch:
        if len(set(self.instruments)) != len(self.instruments):
            raise ValueError("DUPLICATE_CAPTURE_INSTRUMENT")
        for instrument in self.instruments:
            MarketBacktestParameters.model_validate(
                {"instrument": instrument, "interval": self.interval, "days": self.days}
            )
        return self


def execute_history_batch(
    job: Job, repository_path: Path, fabric_root: Path
) -> dict[str, Any]:
    parameters = HistoryCaptureBatch.model_validate(job.parameters)
    captures: list[dict[str, Any]] = []
    for index, instrument in enumerate(parameters.instruments):
        if job.cancel_event.is_set():
            raise ValueError("cancelled")
        # One request at a time; no burst of provider calls from GUI threads.
        if index and job.cancel_event.wait(0.5):
            raise ValueError("cancelled")
        request = MarketBacktestParameters.model_validate(
            {"instrument": instrument, "interval": parameters.interval, "days": parameters.days}
        )
        child = Job(
            job_id=f"{job.job_id}-{index}",
            type="history_capture",
            status=JobStatus.RUNNING,
            created_at=job.created_at,
            parameters=request.model_dump(mode="json"),
            cancel_event=job.cancel_event,
        )
        captures.append(execute_history_capture(child, repository_path, fabric_root))
        job.progress = (index + 1) / len(parameters.instruments)
    return {
        "data_kind": "REAL",
        "input_tier": "EXPLORATORY",
        "instruments": list(parameters.instruments),
        "captures": captures,
        "capture_count": len(captures),
        "historical_availability_verified": False,
        "gate_outcome": "NOT_TESTED",
        "live_trading": False,
        "execution_authority": False,
    }
