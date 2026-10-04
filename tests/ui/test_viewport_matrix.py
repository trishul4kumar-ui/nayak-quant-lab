"""Representative MacBook and desktop sizes remain within the supported policy."""

from __future__ import annotations

import pytest

from quantlab.ui.responsive import ViewportClass, responsive_state


@pytest.mark.parametrize(
    ("width", "height", "expected"),
    [
        (960, 600, ViewportClass.COMPACT_DESKTOP),
        (1024, 640, ViewportClass.COMPACT_DESKTOP),
        (1180, 720, ViewportClass.STANDARD_DESKTOP),
        (1280, 800, ViewportClass.STANDARD_DESKTOP),
        (1366, 768, ViewportClass.STANDARD_DESKTOP),
        (1440, 900, ViewportClass.WIDE_DESKTOP),
        (1512, 982, ViewportClass.WIDE_DESKTOP),
        (1728, 1117, ViewportClass.WIDE_DESKTOP),
        (1920, 1080, ViewportClass.ULTRAWIDE),
        (2560, 1440, ViewportClass.ULTRAWIDE),
    ],
)
def test_viewport_matrix(width: int, height: int, expected: ViewportClass) -> None:
    state = responsive_state(width, height)
    assert state.viewport is expected
    assert state.kpi_columns >= 1
    assert state.terminal_columns >= 1
