from __future__ import annotations

import pytest

from quantlab.capital.budgets import investable_capital, opening_books
from quantlab.capital.definitions import CapitalBooks, CapitalPolicy
from quantlab.capital.errors import CapitalError
from quantlab.capital.library import seed_policy

pytestmark = pytest.mark.capital


def test_investable_respects_cash_floor_and_reservation() -> None:
    policy = seed_policy()
    books = opening_books(policy)
    expected = policy.starting_capital * (1.0 - policy.cash_floor)
    assert books.investable_capital == pytest.approx(expected)
    value = investable_capital(books, policy)
    assert value == pytest.approx(books.investable_capital)
    assert books.note.startswith("research")


def test_reserved_cash_reduces_investable() -> None:
    policy = seed_policy()
    books = CapitalBooks(
        equity=1_000_000,
        cash=1_000_000,
        reserved_cash=200_000,
        investable_capital=0,
    )
    assert investable_capital(books, policy) == pytest.approx(750_000.0)


def test_non_positive_investable_is_an_error() -> None:
    policy = CapitalPolicy(policy_id="x", starting_capital=0, available_capital=0, cash_floor=0)
    books = CapitalBooks(equity=0, cash=0, investable_capital=0)
    with pytest.raises(CapitalError, match="capital_insufficient"):
        investable_capital(books, policy)
