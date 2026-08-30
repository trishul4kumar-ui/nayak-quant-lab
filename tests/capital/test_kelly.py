from __future__ import annotations

import pytest

from quantlab.capital.kelly import apply_fraction, binary_kelly, full_kelly
from quantlab.domain.research import CheckResult

pytestmark = pytest.mark.capital


def test_full_kelly_mu_over_sigma2() -> None:
    result = full_kelly(0.08, 0.04)
    assert result.f_star == pytest.approx(2.0)
    assert result.status is CheckResult.PASS


def test_fractional_kelly_is_capped() -> None:
    result = apply_fraction(full_kelly(0.08, 0.04), 0.25, 0.25)
    assert result.fractional == pytest.approx(0.5)
    assert result.capped == pytest.approx(0.25)


def test_binary_kelly() -> None:
    result = binary_kelly(b=1.0, p=0.6)
    assert result.f_star == pytest.approx(0.2)


def test_unreliable_kelly() -> None:
    result = full_kelly(0.1, 0.0)
    assert result.status is CheckResult.FAIL
    assert result.f_star is None
    assert "KELLY_UNRELIABLE" in result.note
