"""Explicit capital accounting. Capital is never silently equal to portfolio value."""

from __future__ import annotations

from quantlab.capital.definitions import CapitalBooks, CapitalPolicy
from quantlab.capital.errors import CapitalError


def opening_books(policy: CapitalPolicy) -> CapitalBooks:
    equity = policy.starting_capital
    cash = policy.available_capital
    reserved = 0.0
    floor_cash = policy.cash_floor * equity
    investable = max(0.0, min(cash - reserved, equity - reserved - floor_cash))
    return CapitalBooks(
        equity=equity,
        cash=cash,
        reserved_cash=reserved,
        investable_capital=investable,
        available_margin=investable,
        note="research simulated books; not a live broker balance",
    )


def investable_capital(books: CapitalBooks, policy: CapitalPolicy) -> float:
    floor_cash = policy.cash_floor * books.equity
    available = books.cash - books.reserved_cash
    capped = books.equity - books.reserved_cash - floor_cash
    value = max(0.0, min(available, capped))
    if value <= 0:
        raise CapitalError("capital_insufficient: investable capital is non-positive")
    return value


def notionals(weights: dict[str, float], investable: float) -> dict[str, float]:
    return {name: weights[name] * investable for name in sorted(weights)}


def account_gross(weights: dict[str, float], books: CapitalBooks, investable: float) -> float:
    if books.equity <= 0:
        return sum(abs(w) for w in weights.values())
    return sum(abs(w) for w in weights.values()) * investable / books.equity


def account_net(weights: dict[str, float], books: CapitalBooks, investable: float) -> float:
    if books.equity <= 0:
        return sum(weights.values())
    return sum(weights.values()) * investable / books.equity
