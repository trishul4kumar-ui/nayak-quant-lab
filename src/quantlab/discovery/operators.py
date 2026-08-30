"""Operator catalog. Invalid compositions raise DiscoveryError; they are not coerced."""

from __future__ import annotations

from pydantic import BaseModel, Field

from quantlab.discovery.definitions import ExprKind, ValueType


class OperatorSpec(BaseModel):
    op: str
    kind: ExprKind
    input_types: list[ValueType] = Field(default_factory=list)
    output_type: ValueType = ValueType.PANEL
    arity: int = 1
    commutative: bool = False
    lookback: int = 0
    domain: str = "real"
    missing_value_policy: str = "drop"


def operator_library() -> dict[str, OperatorSpec]:
    specs = [
        OperatorSpec(op="feature", kind=ExprKind.FEATURE, arity=0),
        OperatorSpec(op="const", kind=ExprKind.CONSTANT, arity=0, output_type=ValueType.SCALAR),
        OperatorSpec(op="neg", kind=ExprKind.UNARY, domain="real"),
        OperatorSpec(op="abs", kind=ExprKind.UNARY, domain="real"),
        OperatorSpec(op="sign", kind=ExprKind.UNARY, domain="real"),
        OperatorSpec(op="log", kind=ExprKind.UNARY, domain="positive"),
        OperatorSpec(op="exp", kind=ExprKind.UNARY, domain="bounded"),
        OperatorSpec(op="sqrt", kind=ExprKind.UNARY, domain="non_negative"),
        OperatorSpec(
            op="rank", kind=ExprKind.CROSS_SECTION, output_type=ValueType.RANKED_CROSS_SECTION
        ),
        OperatorSpec(op="zscore", kind=ExprKind.CROSS_SECTION),
        OperatorSpec(op="demean", kind=ExprKind.CROSS_SECTION),
        OperatorSpec(op="winsorize", kind=ExprKind.CROSS_SECTION),
        OperatorSpec(op="add", kind=ExprKind.BINARY, arity=2, commutative=True),
        OperatorSpec(op="sub", kind=ExprKind.BINARY, arity=2),
        OperatorSpec(op="mul", kind=ExprKind.BINARY, arity=2, commutative=True),
        OperatorSpec(op="div", kind=ExprKind.BINARY, arity=2, domain="nonzero_divisor"),
        OperatorSpec(op="safe_div", kind=ExprKind.BINARY, arity=2, domain="nonzero_divisor"),
        OperatorSpec(op="min", kind=ExprKind.BINARY, arity=2, commutative=True),
        OperatorSpec(op="max", kind=ExprKind.BINARY, arity=2, commutative=True),
        OperatorSpec(op="rolling_mean", kind=ExprKind.ROLLING, lookback=1),
        OperatorSpec(op="rolling_std", kind=ExprKind.ROLLING, lookback=1),
        OperatorSpec(op="rolling_sum", kind=ExprKind.ROLLING, lookback=1),
        OperatorSpec(op="lag", kind=ExprKind.ROLLING, lookback=1),
        OperatorSpec(op="ewma", kind=ExprKind.ROLLING, lookback=1),
        OperatorSpec(op="change", kind=ExprKind.ROLLING, lookback=1),
    ]
    return {item.op: item for item in specs}


OPERATORS = operator_library()
UNARY_OPS = tuple(s.op for s in OPERATORS.values() if s.kind is ExprKind.UNARY)
CS_OPS = tuple(s.op for s in OPERATORS.values() if s.kind is ExprKind.CROSS_SECTION)
BINARY_OPS = tuple(s.op for s in OPERATORS.values() if s.kind is ExprKind.BINARY)
ROLLING_OPS = tuple(s.op for s in OPERATORS.values() if s.kind is ExprKind.ROLLING)
