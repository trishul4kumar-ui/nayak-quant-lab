"""Decision clock wrapper. Trigger identity is not an order."""

from __future__ import annotations

from datetime import datetime

from quantlab.shadow.enums import TriggerKind
from quantlab.shadow.models import DecisionTrigger
from quantlab.shadow.scheduler import make_trigger


def decision_trigger(
    decision_time: datetime,
    *,
    kind: TriggerKind = TriggerKind.MANUAL_PAPER_RUN,
) -> DecisionTrigger:
    return make_trigger(decision_time=decision_time, kind=kind)
