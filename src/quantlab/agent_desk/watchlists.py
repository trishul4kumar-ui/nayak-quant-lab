"""Frozen desk watchlists; selection is not a trade decision."""

from quantlab.agent_desk.models import Watchlist


def unique_watchlist(value: Watchlist) -> Watchlist:
    value = value.verified()
    if len(set(value.security_ids)) != len(value.security_ids):
        raise ValueError("watchlist securities must be unique")
    return value
