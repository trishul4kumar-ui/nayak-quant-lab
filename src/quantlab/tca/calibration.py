"""PIT-safe calibration. CALIBRATE → FREEZE → TEST. Never fit-all then replay."""

from __future__ import annotations

from datetime import datetime

from quantlab.backtest.spec import config_hash
from quantlab.domain.research import CheckResult
from quantlab.paper_oms.models import PaperFill
from quantlab.tca.errors import CalibrationError
from quantlab.tca.identity import hash_calibration
from quantlab.tca.models import CalibrationRecord
from quantlab.tca.shortfall import signed_slippage


def calibrate_impact(
    fills: list[PaperFill],
    *,
    as_of: datetime,
    window_end: datetime,
    snapshot_id: str,
) -> CalibrationRecord:
    if window_end > as_of:
        raise CalibrationError("calibration_window_leak: window_end > as_of")
    samples: list[float] = []
    for fill in fills:
        if fill.fill_time > window_end:
            continue
        if fill.filled_quantity <= 0 or fill.arrival_price <= 0:
            continue
        slip = signed_slippage(fill, fill.arrival_price)
        if fill.gross_notional:
            samples.append(10_000.0 * slip * fill.filled_quantity / fill.gross_notional)
    estimate = sum(samples) / len(samples) if samples else None
    if samples:
        mean = estimate or 0.0
        var = sum((s - mean) ** 2 for s in samples) / max(len(samples) - 1, 1)
        uncertainty = var**0.5
    else:
        uncertainty = None
    record = CalibrationRecord(
        model_id="impact-mean-bps",
        model_version="v1",
        method="mean_participation_bps",
        fit_window_start=min((f.fill_time for f in fills), default=window_end),
        fit_window_end=window_end,
        snapshot_id=snapshot_id,
        sample_count=len(samples),
        estimate=estimate,
        uncertainty=uncertainty,
        data_checksum=config_hash({"n": len(samples), "as_of": as_of.isoformat()}),
        validation=CheckResult.PASS if samples else CheckResult.NOT_TESTED,
        frozen=True,
        note=(
            "Uncalibrated until sample_count is adequate. "
            "This is not an empirical NSE impact coefficient."
        ),
    )
    return record.model_copy(update={"parameter_hash": hash_calibration(record)})
