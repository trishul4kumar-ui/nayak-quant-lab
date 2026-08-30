"""Explicit cost schedule. Official Indian fee tables are not invented here."""

from __future__ import annotations

from pydantic import BaseModel, model_validator


class CostSchedule(BaseModel):
    """Proportional bps on turnover. Unspecified Indian taxes stay 0 with provenance."""

    commission_bps: float = 10.0
    exchange_fees_bps: float = 0.0
    stt_bps: float = 0.0
    stamp_duty_bps: float = 0.0
    gst_bps: float = 0.0
    sebi_bps: float = 0.0
    provenance: str = "research_default_10bps_commission_other_legs_unspecified"

    @model_validator(mode="after")
    def _non_negative(self) -> CostSchedule:
        for name in (
            "commission_bps",
            "exchange_fees_bps",
            "stt_bps",
            "stamp_duty_bps",
            "gst_bps",
            "sebi_bps",
        ):
            if float(getattr(self, name)) < 0:
                raise ValueError(f"{name} cannot be negative")
        return self

    def total_bps(self) -> float:
        return (
            self.commission_bps
            + self.exchange_fees_bps
            + self.stt_bps
            + self.stamp_duty_bps
            + self.gst_bps
            + self.sebi_bps
        )


RESEARCH_COST_GRID_BPS: tuple[float, ...] = (5.0, 10.0, 20.0, 50.0, 100.0)
