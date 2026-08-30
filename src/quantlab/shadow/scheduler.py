"""Decision triggers. Duplicate timestamps are idempotent, not a second stream."""

from __future__ import annotations

from datetime import datetime

from quantlab.shadow.enums import TriggerKind
from quantlab.shadow.models import DecisionTrigger


def make_trigger(
    *,
    decision_time: datetime,
    kind: TriggerKind = TriggerKind.MANUAL_PAPER_RUN,
    trigger_id: str = "",
) -> DecisionTrigger:
    stamp = decision_time.isoformat()
    return DecisionTrigger(
        trigger_id=trigger_id or f"TRG-{kind.value}-{stamp}",
        trigger_time=decision_time,
        source=kind,
        decision_time=decision_time,
    )
