from __future__ import annotations

import pytest

from quantlab.app.settings_store import ExperienceMode
from quantlab.ui.navigation import (
    FULL_NAV,
    NavItem,
    filter_nav_items,
    nav_for_mode,
    nav_item_matches,
)


@pytest.mark.desktop
def test_nav_item_matches_aliases() -> None:
    market = NavItem("market", "Market")
    assert nav_item_matches(market, "watchlist")
    assert nav_item_matches(market, "market")
    assert not nav_item_matches(market, "portfolio")


@pytest.mark.desktop
def test_filter_nav_items_finds_validation() -> None:
    items = nav_for_mode(ExperienceMode.FULL)
    filtered = filter_nav_items(items, "validate")
    keys = [item.key for item in filtered if not item.header]
    assert "validation" in keys


@pytest.mark.desktop
def test_filter_nav_items_empty_query_returns_all() -> None:
    items = nav_for_mode(ExperienceMode.FULL)
    assert len(filter_nav_items(items, "")) == len(items)


@pytest.mark.desktop
def test_filter_nav_no_matches_header() -> None:
    items = list(FULL_NAV)
    filtered = filter_nav_items(items, "zzznomatch")
    assert len(filtered) == 1
    assert filtered[0].header
