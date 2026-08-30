"""PIT factor engine. Wraps features or equal-weight beta. Does not invent fundamentals."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from quantlab.alpha.ensemble import apply_sign
from quantlab.core.errors import AlignmentError, FactorError
from quantlab.core.identifiers import InstrumentId
from quantlab.domain.models import OHLCVBar
from quantlab.domain.research import CheckResult
from quantlab.factors.definition import FactorDefinition, FactorSource
from quantlab.factors.market import beta_panel
from quantlab.features.engine import Panel, compute_panel, session_calendar
from quantlab.features.normalize import apply_cross_section, winsorize_cs
from quantlab.features.registry import get_feature


class FactorObservation(BaseModel):
    factor_id: str
    version: str
    as_of: datetime
    status: CheckResult
    n: int = 0
    identity_hash: str = ""
    note: str = ""


def compute_factor_panel(
    definition: FactorDefinition,
    bars: dict[InstrumentId, list[OHLCVBar]],
    dates: list[datetime] | None = None,
) -> tuple[Panel, FactorObservation]:
    calendar = dates or session_calendar(bars)
    last = calendar[-1] if calendar else datetime.min
    if definition.source is FactorSource.NOT_IMPLEMENTED:
        return {}, FactorObservation(
            factor_id=definition.factor_id,
            version=definition.version,
            as_of=last,
            status=CheckResult.NOT_TESTED,
            identity_hash=definition.identity_hash(),
            note=definition.notes or "NOT_TESTED: required PIT inputs are not bundled",
        )
    if definition.source is FactorSource.EQUAL_WEIGHT_MARKET_BETA:
        panel = beta_panel(bars, calendar, lookback=definition.lookback)
        status = CheckResult.PASS if panel else CheckResult.NOT_TESTED
        return panel, FactorObservation(
            factor_id=definition.factor_id,
            version=definition.version,
            as_of=last,
            status=status,
            n=_n(panel),
            identity_hash=definition.identity_hash(),
            note="equal-weight universe beta; not NIFTY",
        )
    if definition.source is FactorSource.FEATURE:
        if not definition.feature_id:
            raise FactorError(f"{definition.factor_id} is missing feature_id")
        feature = get_feature(definition.feature_id)
        raw = compute_panel(feature, bars, calendar)
        panel = _postprocess(raw, definition)
        return panel, FactorObservation(
            factor_id=definition.factor_id,
            version=definition.version,
            as_of=last,
            status=CheckResult.PASS if panel else CheckResult.NOT_TESTED,
            n=_n(panel),
            identity_hash=definition.identity_hash(),
            note=f"from feature {definition.feature_id}@{feature.version}",
        )
    if definition.source is FactorSource.RESIDUAL:
        raise FactorError(
            f"{definition.factor_id} is a residual identity; compute via residualize_panel"
        )
    raise FactorError(f"unsupported factor source {definition.source}")


def _postprocess(panel: Panel, definition: FactorDefinition) -> Panel:
    out: Panel = {}
    for as_of, row in panel.items():
        finite = _finite(row, as_of)
        if not finite:
            continue
        if definition.winsorization.startswith("winsor"):
            finite = winsorize_cs(finite)
        scaled = apply_cross_section(finite, definition.normalization)
        out[as_of] = apply_sign(scaled, definition.expected_direction)
    return out


def _finite(row: dict[str, float], as_of: datetime) -> dict[str, float]:
    clean: dict[str, float] = {}
    for key, value in row.items():
        if value != value or value in {float("inf"), float("-inf")}:
            raise AlignmentError(f"non-finite factor value for {key} at {as_of.isoformat()}")
        clean[key] = value
    return clean


def _n(panel: Panel) -> int:
    return sum(len(row) for row in panel.values())
