from __future__ import annotations

import pytest

from quantlab.capital.library import seed_policy, seed_request
from quantlab.capital.memory import reset

pytestmark = pytest.mark.capital


@pytest.fixture(autouse=True)
def _reset_capital_store() -> None:
    reset()
    yield
    reset()


@pytest.fixture
def policy():
    return seed_policy()


@pytest.fixture
def request_():
    return seed_request()
