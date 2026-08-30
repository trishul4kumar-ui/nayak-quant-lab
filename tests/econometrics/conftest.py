import pytest

from quantlab.econometrics.state import reset as reset_econo


@pytest.fixture(autouse=True)
def _reset() -> None:
    reset_econo()
