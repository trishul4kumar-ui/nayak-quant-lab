"""Return calculations. Do not annualize without enough observations."""

from __future__ import annotations

import math

from quantlab.domain.research import CheckResult
from quantlab.monitoring.enums import ReturnKind
from quantlab.monitoring.models import ReturnReport


def simple_return(beginning: float, ending: float) -> float | None:
    if beginning == 0:
        return None
    return (ending / beginning) - 1.0


def log_return(beginning: float, ending: float) -> float | None:
    if beginning <= 0 or ending <= 0:
        return None
    return math.log(ending / beginning)


def cumulative_from_simple(returns: list[float]) -> float:
    acc = 1.0
    for item in returns:
        acc *= 1.0 + item
    return acc - 1.0


def time_weighted(period_returns: list[float]) -> float | None:
    if not period_returns:
        return None
    return cumulative_from_simple(period_returns)


def money_weighted(
    cashflows: list[tuple[float, float]],
    ending: float,
) -> float | None:
    """IRR-style money-weighted return. cashflows are (time_fraction, amount)."""
    if not cashflows:
        return None
    if len(cashflows) == 1 and cashflows[0][1] != 0:
        start = cashflows[0][1]
        if start == 0:
            return None
        return (ending / start) - 1.0
    return None


def rolling_volatility(returns: list[float]) -> float | None:
    if len(returns) < 2:
        return None
    mean = sum(returns) / len(returns)
    var = sum((item - mean) ** 2 for item in returns) / (len(returns) - 1)
    return math.sqrt(var)


def rolling_sharpe(
    returns: list[float],
    *,
    risk_free: float,
) -> float | None:
    vol = rolling_volatility(returns)
    if vol is None or vol == 0:
        return None
    mean = sum(returns) / len(returns)
    return (mean - risk_free) / vol


def downside_deviation(returns: list[float], *, mar: float = 0.0) -> float | None:
    downside = [item for item in returns if item < mar]
    if len(downside) < 2:
        return None
    mean = sum(downside) / len(downside)
    var = sum((item - mean) ** 2 for item in downside) / (len(downside) - 1)
    return math.sqrt(var)


def report_returns(
    *,
    beginning: float,
    ending: float,
    period_returns: list[float],
    risk_free: float,
) -> list[ReturnReport]:
    simple = simple_return(beginning, ending)
    log_r = log_return(beginning, ending)
    twr = time_weighted(period_returns) if len(period_returns) >= 1 else simple
    mwr = money_weighted([(0.0, beginning)], ending)
    enough = len(period_returns) >= 20
    rows = [
        ReturnReport(
            kind=ReturnKind.SIMPLE,
            value=simple,
            status=CheckResult.PASS if simple is not None else CheckResult.NOT_TESTED,
            annualized=None if not enough else (
                (1.0 + simple) ** (252 / max(len(period_returns), 1)) - 1.0
                if simple is not None
                else None
            ),
            note="Annualization withheld unless >= 20 observations.",
        ),
        ReturnReport(
            kind=ReturnKind.LOG,
            value=log_r,
            status=CheckResult.PASS if log_r is not None else CheckResult.NOT_TESTED,
        ),
        ReturnReport(
            kind=ReturnKind.CUMULATIVE,
            value=twr,
            status=CheckResult.PASS if twr is not None else CheckResult.NOT_TESTED,
        ),
        ReturnReport(
            kind=ReturnKind.TIME_WEIGHTED,
            value=twr,
            status=CheckResult.PASS if twr is not None else CheckResult.NOT_TESTED,
        ),
        ReturnReport(
            kind=ReturnKind.MONEY_WEIGHTED,
            value=mwr,
            status=CheckResult.PASS if mwr is not None else CheckResult.NOT_TESTED,
            note="Single-period MWR equals simple return when one cashflow.",
        ),
    ]
    del risk_free
    return rows
