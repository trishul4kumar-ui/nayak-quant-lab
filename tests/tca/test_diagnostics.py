from __future__ import annotations

import pytest

from quantlab.app.tca import (
    capacity_payload,
    compare_payload,
    fragility_payload,
    report_payload,
    run_payload,
    shortfall_payload,
    stress_payload,
)
from quantlab.domain.research import CheckResult
from quantlab.tca.enums import FragilityStatus
from quantlab.tca.fragility import fragility_from
from quantlab.tca.models import CapacityResult, ShortfallBreakdown
from quantlab.tca.sensitivity import scale_shortfall
from quantlab.tca.uncertainty import interval


@pytest.mark.parametrize("factor", [0.5, 1.0, 1.5, 2.0, 3.0])
def test_sensitivity_scale(factor: float) -> None:
    item = ShortfallBreakdown(total=10.0, status=CheckResult.PASS)
    assert scale_shortfall(item, factor) == pytest.approx(10.0 * factor)


def test_uncertainty_interval() -> None:
    assert "NOT_TESTED" in interval(None, None)
    assert "±" in interval(1.0, 0.2)


@pytest.mark.parametrize(
    "status",
    list(FragilityStatus),
)
def test_fragility_enum(status: FragilityStatus) -> None:
    assert status.value


def test_fragility_not_tested_without_shortfall() -> None:
    from quantlab.tca.enums import CapacityStatus

    out = fragility_from(
        ShortfallBreakdown(status=CheckResult.NOT_TESTED),
        CapacityResult(policy_id="p", status=CapacityStatus.NOT_TESTED),
    )
    assert out.status is FragilityStatus.NOT_TESTED


@pytest.mark.parametrize(
    "fn",
    [
        run_payload,
        shortfall_payload,
        capacity_payload,
        fragility_payload,
        compare_payload,
        report_payload,
        stress_payload,
    ],
)
def test_app_payloads(fn) -> None:
    out = fn()
    assert out is not None
