import pytest

from quantlab.certification.state import reset as reset_cert
from quantlab.econometrics.state import reset as reset_econo
from quantlab.monitoring.state import reset as reset_monitoring
from quantlab.paper_oms.state import reset as reset_paper
from quantlab.tca.state import reset as reset_tca


@pytest.fixture(autouse=True)
def _reset() -> None:
    reset_paper()
    reset_monitoring()
    reset_tca()
    reset_econo()
    reset_cert()
