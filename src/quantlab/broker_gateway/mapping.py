"""Security-master mapping. Ambiguity fails closed. No silent ticker mapping."""

from __future__ import annotations

from quantlab.broker_gateway.models import InstrumentMapping


def resolve_mapping(
    mappings: tuple[InstrumentMapping, ...],
    *,
    broker_instrument_id: str,
) -> InstrumentMapping | None:
    matches = [item for item in mappings if item.broker_instrument_id == broker_instrument_id]
    if len(matches) != 1:
        return None
    item = matches[0]
    if item.ambiguous or item.mapping_confidence == "low":
        return None
    return item


def mapping_is_ambiguous(mappings: tuple[InstrumentMapping, ...]) -> bool:
    ids = [item.broker_instrument_id for item in mappings]
    return any(item.ambiguous for item in mappings) or len(ids) != len(set(ids))
