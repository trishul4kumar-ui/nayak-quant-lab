"""Manual researcher interventions. Silent edits are prohibited."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field


class Intervention(BaseModel):
    kind: str
    detail: str
    at: datetime = Field(default_factory=lambda: datetime.now(tz=UTC))
    experiment_id: str = ""
    family_id: str = ""


class InterventionLog(BaseModel):
    events: list[Intervention] = Field(default_factory=list)

    def record(
        self,
        kind: str,
        detail: str,
        *,
        experiment_id: str = "",
        family_id: str = "",
    ) -> Intervention:
        event = Intervention(
            kind=kind,
            detail=detail,
            experiment_id=experiment_id,
            family_id=family_id,
        )
        self.events.append(event)
        return event
