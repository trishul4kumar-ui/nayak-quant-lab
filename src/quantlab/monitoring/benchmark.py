"""Benchmarks without inventing NIFTY history."""

from __future__ import annotations

from quantlab.domain.research import CheckResult
from quantlab.monitoring.enums import BenchmarkKind
from quantlab.monitoring.models import BenchmarkSeries
from quantlab.monitoring.returns import simple_return
from quantlab.paper_oms.models import PaperAccount, PaperMarketSnapshot


def equal_weight_universe(
    snapshot: PaperMarketSnapshot,
    account: PaperAccount,
    *,
    beginning_equity: float,
) -> BenchmarkSeries:
    names = [n for n, ok in snapshot.tradable.items() if ok]
    if not names or beginning_equity <= 0:
        return BenchmarkSeries(
            benchmark_id="ew-unavailable",
            kind=BenchmarkKind.UNAVAILABLE,
            status=CheckResult.NOT_TESTED,
            note="Equal-weight universe needs tradable names and capital.",
        )
    # Diagnostic: equal-weight of names that have a current mark vs purchase.
    rets: list[float] = []
    for name in names:
        pos = account.positions.get(name)
        mark = snapshot.prices.get(name, 0.0)
        if pos is not None and pos.average_cost > 0 and mark > 0:
            rets.append(mark / pos.average_cost - 1.0)
    port = simple_return(beginning_equity, account.equity)
    bench = sum(rets) / len(rets) if rets else None
    relative = None if port is None or bench is None else port - bench
    return BenchmarkSeries(
        benchmark_id="ew-universe-synthetic",
        kind=BenchmarkKind.EQUAL_WEIGHT_UNIVERSE,
        returns=rets,
        relative_return=relative,
        status=CheckResult.PASS if rets else CheckResult.NOT_TESTED,
        note=(
            "Internal equal-weight diagnostic on the paper snapshot. "
            "Not NIFTY. Not an official index. BENCHMARK RELATIVE vs ABSOLUTE."
        ),
    )


def user_benchmark(
    returns: list[float],
    *,
    portfolio_return: float | None,
) -> BenchmarkSeries:
    bench = sum(returns) / len(returns) if returns else None
    relative = None if portfolio_return is None or bench is None else (
        portfolio_return - bench
    )
    return BenchmarkSeries(
        benchmark_id="user-supplied",
        kind=BenchmarkKind.USER_SUPPLIED,
        returns=list(returns),
        relative_return=relative,
        status=CheckResult.PASS if returns else CheckResult.NOT_TESTED,
        note="User-supplied benchmark series. Not NIFTY unless the user sourced it.",
    )


def nifty_placeholder() -> BenchmarkSeries:
    return BenchmarkSeries(
        benchmark_id="nifty-not-tested",
        kind=BenchmarkKind.INDEX,
        status=CheckResult.NOT_TESTED,
        note="Official NIFTY/index history is not fabricated.",
    )
