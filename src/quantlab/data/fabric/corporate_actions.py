"""Corporate actions. Missing announcement times are unavailable — never invented."""

from __future__ import annotations

import math
from datetime import datetime

from pydantic import BaseModel

from quantlab.core.errors import DataIntegrityError
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
        if self.available_time.utcoffset() is None or as_of.utcoffset() is None:
            raise DataIntegrityError("corporate-action times must be timezone-aware")
        return self.available_time <= as_of


def split_factor(action: CorporateAction) -> float:
    if action.event_type is not CorporateActionType.SPLIT:
        return 1.0
    if action.ratio is None or not math.isfinite(action.ratio) or action.ratio <= 0:
        raise ValueError(f"{action.action_id} split requires positive ratio")
    return action.ratio


def apply_backward_splits(
    bars: list[OHLCVBar],
    actions: list[CorporateAction],
    *,
    as_of: datetime,
) -> list[OHLCVBar]:
    """Restate history using only split revisions known and effective at as_of.

    The supplied action list does not establish complete corporate-action
    coverage. The caller must separately verify source and coverage evidence.
    """
    if as_of.utcoffset() is None:
        raise DataIntegrityError("corporate-action cutoff must be timezone-aware")
    securities = {str(bar.instrument) for bar in bars}
    for bar in bars:
        if bar.pit.event_time.utcoffset() is None or bar.pit.event_time > as_of:
            raise DataIntegrityError("bar event time is invalid or later than the cutoff")
        if bar.pit.available_time.utcoffset() is None or bar.pit.available_time > as_of:
            raise DataIntegrityError("bar availability is invalid or later than the cutoff")

    revisions: dict[str, CorporateAction] = {}
    identities: dict[str, tuple[str, CorporateActionType]] = {}
    for action in actions:
        if (
            action.event_type is not CorporateActionType.SPLIT
            or action.security_id not in securities
        ):
            continue
        if not action.action_id.strip() or not action.source.strip():
            raise DataIntegrityError("corporate action requires identity and source")
        if action.available_time is None:
            raise DataIntegrityError("corporate-action availability is unknown")
        if action.announcement_time is not None:
            if action.announcement_time.utcoffset() is None:
                raise DataIntegrityError("corporate-action announcement must be timezone-aware")
            if (
                action.available_time.utcoffset() is None
                or action.available_time < action.announcement_time
            ):
                raise DataIntegrityError("action availability precedes its announcement")
        identity = (action.security_id, action.event_type)
        if identities.setdefault(action.action_id, identity) != identity:
            raise DataIntegrityError("corporate-action revisions change identity")
        if not action.is_knowable_at(as_of):
            continue
        previous = revisions.get(action.action_id)
        if previous is not None and previous.available_time == action.available_time:
            if previous != action:
                raise DataIntegrityError("conflicting corporate-action revisions")
            continue
        if previous is None or (
            previous.available_time is not None
            and action.available_time is not None
            and previous.available_time < action.available_time
        ):
            revisions[action.action_id] = action

    known: list[CorporateAction] = []
    for action in revisions.values():
        if action.effective_date is None or action.effective_date.utcoffset() is None:
            raise DataIntegrityError("known split lacks a timezone-aware effective date")
        if action.effective_date <= as_of:
            split_factor(action)
            known.append(action)
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
