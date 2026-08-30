"""Corporate actions. Missing announcement times are unavailable — never invented."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from quantlab.data.fabric.types import CorporateActionType, PriceKind
from quantlab.domain.models import OHLCVBar


class CorporateAction(BaseModel):
    action_id: str
    security_id: str
    event_type: CorporateActionType
    source: str
    announcement_time: datetime | None = None
    record_date: datetime | None = None
    ex_date: datetime | None = None
    effective_date: datetime | None = None
    payment_date: datetime | None = None
    ratio: float | None = None
    value: float | None = None
    available_time: datetime | None = None

    def is_knowable_at(self, as_of: datetime) -> bool:
        if self.available_time is None:
            return False
        return self.available_time <= as_of


def split_factor(action: CorporateAction) -> float:
    if action.event_type is not CorporateActionType.SPLIT:
        return 1.0
    if action.ratio is None or action.ratio <= 0:
        raise ValueError(f"{action.action_id} split requires positive ratio")
    return action.ratio


def apply_backward_splits(
    bars: list[OHLCVBar],
    actions: list[CorporateAction],
    *,
    as_of: datetime,
) -> list[OHLCVBar]:
    """Restate pre-split history onto the price basis knowable at as_of."""
    known = [
        a
        for a in actions
        if a.event_type is CorporateActionType.SPLIT
        and a.is_knowable_at(as_of)
        and a.effective_date is not None
    ]
    out: list[OHLCVBar] = []
    for bar in bars:
        key = str(bar.instrument)
        factor = 1.0
        for action in known:
            if action.security_id != key:
                continue
            assert action.effective_date is not None
            if bar.pit.event_time < action.effective_date:
                factor *= split_factor(action)
        if factor == 1.0:
            out.append(bar.model_copy(update={"price_kind": PriceKind.ADJUSTED_PRICE.value}))
            continue
        out.append(
            bar.model_copy(
                update={
                    "open": bar.open / factor,
                    "high": bar.high / factor,
                    "low": bar.low / factor,
                    "close": bar.close / factor,
                    "price_kind": PriceKind.ADJUSTED_PRICE.value,
                }
            )
        )
    return out
