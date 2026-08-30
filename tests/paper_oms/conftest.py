from __future__ import annotations

import pytest

from quantlab.paper_oms.state import reset

pytestmark = pytest.mark.paper_oms


@pytest.fixture(autouse=True)
def _reset_paper_oms() -> None:
    reset()
    yield
    reset()
