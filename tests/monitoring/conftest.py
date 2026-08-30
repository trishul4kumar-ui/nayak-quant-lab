import pytest

from quantlab.monitoring.state import reset as reset_monitoring
from quantlab.paper_oms.state import reset as reset_paper
from quantlab.tca.state import reset as reset_tca


@pytest.fixture(autouse=True)
def _reset_engines() -> None:
    reset_paper()
    reset_monitoring()
    reset_tca()
