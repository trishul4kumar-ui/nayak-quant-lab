"""Explicit cost legs. Official Indian fee tables are not invented here."""

from __future__ import annotations

from quantlab.backtest.costs import CostSchedule
from quantlab.execution_research.definition import CostComponent, CostStatus


def explicit_bps(schedule: CostSchedule) -> float:
    return float(schedule.total_bps())


def cost_components(schedule: CostSchedule) -> list[CostComponent]:
    unspecified = {
        "exchange_fees_bps",
        "stt_bps",
        "stamp_duty_bps",
        "gst_bps",
        "sebi_bps",
    }
    rows: list[CostComponent] = []
    for name in (
        "commission_bps",
        "exchange_fees_bps",
        "stt_bps",
        "stamp_duty_bps",
        "gst_bps",
        "sebi_bps",
    ):
        value = float(getattr(schedule, name))
        status = (
            CostStatus.UNSPECIFIED
            if name in unspecified and value == 0.0
            else CostStatus.CONFIGURED
        )
        rows.append(
            CostComponent(
                name=name,
                value=value,
                unit="bps",
                provenance=schedule.provenance,
                status=status,
            )
        )
    return rows
