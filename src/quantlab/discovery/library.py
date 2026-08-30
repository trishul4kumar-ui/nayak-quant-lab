"""Seed expression library. Distinct from the Prompt 06 feature library."""

from __future__ import annotations

from quantlab.discovery.expression import ExprNode
from quantlab.discovery.generator import seed_expressions
from quantlab.discovery.grammar import GrammarSpec


def seed_library(grammar: GrammarSpec | None = None) -> list[ExprNode]:
    return seed_expressions(grammar)
