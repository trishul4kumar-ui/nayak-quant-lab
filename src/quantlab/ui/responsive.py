"""Shared, content-width based responsive rules for the desktop workstation.

The application is a desktop product, not a shrunken website.  These rules keep
dense research surfaces useful on a MacBook by choosing a layout before widgets
are squeezed below their operating width.  Pages receive a single
``ResponsiveState`` instead of duplicating arbitrary pixel checks.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ViewportClass(StrEnum):
    COMPACT_DESKTOP = "compact_desktop"
    STANDARD_DESKTOP = "standard_desktop"
    WIDE_DESKTOP = "wide_desktop"
    ULTRAWIDE = "ultrawide"


@dataclass(frozen=True)
class ResponsiveState:
    """Resolved layout decisions for the currently available page content width."""

    content_width: int
    content_height: int
    viewport: ViewportClass
    sidebar_icon_rail: bool
    toolbar_stacked: bool
    kpi_columns: int
    terminal_columns: int
    terminal_panel_minimum: int
    master_detail_vertical: bool
    table_compact: bool
    chart_minimum_height: int


def responsive_state(content_width: int, content_height: int = 0) -> ResponsiveState:
    """Resolve layout policy from logical content pixels, never monitor pixels."""

    width = max(0, content_width)
    height = max(0, content_height)
    if width < 1100:
        viewport = ViewportClass.COMPACT_DESKTOP
        return ResponsiveState(
            content_width=width,
            content_height=height,
            viewport=viewport,
            sidebar_icon_rail=True,
            toolbar_stacked=True,
            kpi_columns=1 if width < 680 else 2,
            terminal_columns=1,
            terminal_panel_minimum=360,
            master_detail_vertical=True,
            table_compact=True,
            chart_minimum_height=200,
        )
    if width < 1440:
        viewport = ViewportClass.STANDARD_DESKTOP
        return ResponsiveState(
            content_width=width,
            content_height=height,
            viewport=viewport,
            sidebar_icon_rail=False,
            toolbar_stacked=False,
            kpi_columns=3 if width < 1240 else 4,
            terminal_columns=2,
            terminal_panel_minimum=400,
            master_detail_vertical=False,
            table_compact=False,
            chart_minimum_height=220,
        )
    if width < 1920:
        viewport = ViewportClass.WIDE_DESKTOP
        return ResponsiveState(
            content_width=width,
            content_height=height,
            viewport=viewport,
            sidebar_icon_rail=False,
            toolbar_stacked=False,
            kpi_columns=4,
            terminal_columns=2,
            terminal_panel_minimum=420,
            master_detail_vertical=False,
            table_compact=False,
            chart_minimum_height=240,
        )
    return ResponsiveState(
        content_width=width,
        content_height=height,
        viewport=ViewportClass.ULTRAWIDE,
        sidebar_icon_rail=False,
        toolbar_stacked=False,
        kpi_columns=4,
        terminal_columns=3,
        terminal_panel_minimum=420,
        master_detail_vertical=False,
        table_compact=False,
        chart_minimum_height=260,
    )


def valid_splitter_sizes(sizes: object, expected_count: int) -> list[int] | None:
    """Reject stale/pathological persisted splitter values before applying them."""

    if not isinstance(sizes, list) or len(sizes) != expected_count:
        return None
    if not all(isinstance(size, int) and size >= 24 for size in sizes):
        return None
    total = sum(sizes)
    if total <= 0:
        return None
    smallest = min(sizes)
    if expected_count > 1 and smallest / total < 0.04:
        return None
    return list(sizes)
