"""Benchmark abstraction. Official index history is never fabricated."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from pydantic import BaseModel

from quantlab.domain.research import CheckResult
from quantlab.math.metrics import simple_returns, volatility


class Benchmark(Protocol):
    name: str

    def equity(self, dates: list[datetime], initial: float) -> list[float] | None: ...


class CashBenchmark:
    name = "cash_zero_rf"

    def equity(self, dates: list[datetime], initial: float) -> list[float] | None:
        if not dates:
            return None
        return [initial] * len(dates)


class UnavailableBenchmark:
    name = "unavailable"

    def equity(self, dates: list[datetime], initial: float) -> list[float] | None:
        return None


class BenchmarkReport(BaseModel):
    schema_version: str = "1"
    name: str
    status: CheckResult
    strategy_return: float | None = None
    benchmark_return: float | None = None
    excess_return: float | None = None
    tracking_error: float | None = None
    information_ratio: float | None = None
    note: str = ""


def evaluate_benchmark(
    strategy_equity: list[float],
    dates: list[datetime],
    benchmark: Benchmark,
    initial: float,
) -> BenchmarkReport:
    series = benchmark.equity(dates, initial)
    if series is None or len(strategy_equity) < 2:
        return BenchmarkReport(
            name=benchmark.name,
            status=CheckResult.NOT_TESTED,
            note="no benchmark series; NIFTY/Sensex history is not bundled",
        )
    strat = strategy_equity[-1] / strategy_equity[0] - 1.0 if strategy_equity[0] > 0 else 0.0
    bench = series[-1] / series[0] - 1.0 if series[0] > 0 else 0.0
    s_rets = simple_returns(strategy_equity)
    b_rets = simple_returns(series)
    n = min(len(s_rets), len(b_rets))
    excess = [s_rets[i] - b_rets[i] for i in range(n)]
    te = volatility(excess) if n >= 2 else None
    ir: float | None = None
    if n >= 2:
        mean_ex = sum(excess) / n
        std = (sum((x - mean_ex) ** 2 for x in excess) / n) ** 0.5
        ir = 0.0 if std == 0.0 else mean_ex / std
    return BenchmarkReport(
        name=benchmark.name,
        status=CheckResult.PASS,
        strategy_return=strat,
        benchmark_return=bench,
        excess_return=strat - bench,
        tracking_error=te,
        information_ratio=ir,
        note="cash benchmark is a zero-rf convention, not an Indian T-bill",
    )
