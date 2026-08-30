"""PIT expression evaluation. Uses existing feature panels; never labels as inputs."""

from __future__ import annotations

import math
from datetime import datetime

from quantlab.discovery.definitions import ExprKind
from quantlab.discovery.errors import DiscoveryError
from quantlab.discovery.expression import ExprNode
from quantlab.discovery.primitives import assert_not_label
from quantlab.features.engine import Panel
from quantlab.features.registry import get_feature

EPS = 1e-12


def slice_panel(panel: Panel, dates: list[datetime]) -> Panel:
    allowed = set(dates)
    return {ts: row for ts, row in panel.items() if ts in allowed}


def evaluate_expression(
    expr: ExprNode,
    feature_panels: dict[str, Panel],
    cache: dict[str, Panel] | None = None,
) -> Panel:
    if expr.uses_forbidden_label():
        raise DiscoveryError("label entered expression evaluation")
    store = cache if cache is not None else {}
    key = expr.identity_hash()
    if key in store:
        return store[key]
    panel = _eval(expr, feature_panels, store)
    store[key] = panel
    return panel


def _eval(expr: ExprNode, features: dict[str, Panel], cache: dict[str, Panel]) -> Panel:
    if expr.kind is ExprKind.FEATURE:
        assert_not_label(expr.name)
        if expr.name not in features:
            get_feature(expr.name)
            raise DiscoveryError(f"feature panel missing: {expr.name}")
        return features[expr.name]
    if expr.kind is ExprKind.CONSTANT:
        raise DiscoveryError("bare constant is not a cross-section expression")
    kids = expr.children
    if expr.kind is ExprKind.BINARY:
        left = evaluate_expression(kids[0], features, cache)
        if kids[1].kind is ExprKind.CONSTANT:
            return _binary_const(expr.op, left, float(kids[1].constant or 0.0))
        if kids[0].kind is ExprKind.CONSTANT:
            right = evaluate_expression(kids[1], features, cache)
            return _binary_const(expr.op, right, float(kids[0].constant or 0.0))
        right = evaluate_expression(kids[1], features, cache)
        return _binary(expr.op, left, right, kids[1])
    child_panel = evaluate_expression(kids[0], features, cache)
    if expr.op in {"rank", "zscore", "demean", "winsorize"}:
        return _cross_section(expr.op, child_panel)
    if expr.kind is ExprKind.ROLLING:
        return _rolling(expr.op, child_panel, expr.window)
    return _unary(expr.op, child_panel)


def _unary(op: str, panel: Panel) -> Panel:
    out: Panel = {}
    for ts, row in panel.items():
        new_row: dict[str, float] = {}
        for name, value in row.items():
            mapped = _unary_value(op, value)
            if mapped is not None:
                new_row[name] = mapped
        if new_row:
            out[ts] = new_row
    return out


def _unary_value(op: str, value: float) -> float | None:
    if op == "neg":
        return -value
    if op == "abs":
        return abs(value)
    if op == "sign":
        if value > 0:
            return 1.0
        if value < 0:
            return -1.0
        return 0.0
    if op == "log":
        if value <= EPS:
            return None
        return math.log(value)
    if op == "sqrt":
        if value < 0:
            return None
        return math.sqrt(value)
    if op == "exp":
        if value > 20:
            return None
        return math.exp(value)
    raise DiscoveryError(f"unknown unary {op}")


def _binary(op: str, left: Panel, right: Panel, right_node: ExprNode) -> Panel:
    if right_node.kind is ExprKind.CONSTANT:
        const = float(right_node.constant or 0.0)
        return _binary_const(op, left, const)
    dates = sorted(set(left) & set(right))
    out: Panel = {}
    for ts in dates:
        row: dict[str, float] = {}
        a = left[ts]
        b = right[ts]
        for name in set(a) & set(b):
            mapped = _binary_value(op, a[name], b[name])
            if mapped is not None:
                row[name] = mapped
        if row:
            out[ts] = row
    return out


def _binary_const(op: str, left: Panel, const: float) -> Panel:
    out: Panel = {}
    for ts, row in left.items():
        new_row: dict[str, float] = {}
        for name, value in row.items():
            mapped = _binary_value(op, value, const)
            if mapped is not None:
                new_row[name] = mapped
        if new_row:
            out[ts] = new_row
    return out


def _binary_value(op: str, left: float, right: float) -> float | None:
    if op == "add":
        return left + right
    if op == "sub":
        return left - right
    if op == "mul":
        return left * right
    if op in {"div", "safe_div"}:
        if abs(right) < EPS:
            return None
        return left / right
    if op == "min":
        return min(left, right)
    if op == "max":
        return max(left, right)
    raise DiscoveryError(f"unknown binary {op}")


def _cross_section(op: str, panel: Panel) -> Panel:
    out: Panel = {}
    for ts, row in panel.items():
        if len(row) < 3:
            continue
        if op == "rank":
            ordered = sorted(row.items(), key=lambda item: item[1])
            denom = max(len(ordered) - 1, 1)
            out[ts] = {name: i / denom for i, (name, _) in enumerate(ordered)}
            continue
        values = list(row.values())
        mean = sum(values) / len(values)
        if op == "demean":
            out[ts] = {name: value - mean for name, value in row.items()}
            continue
        var = sum((value - mean) ** 2 for value in values) / len(values)
        std = math.sqrt(var)
        if op == "zscore":
            if std < EPS:
                continue
            out[ts] = {name: (value - mean) / std for name, value in row.items()}
            continue
        if op == "winsorize":
            lo = _quantile(values, 0.05)
            hi = _quantile(values, 0.95)
            out[ts] = {name: min(max(value, lo), hi) for name, value in row.items()}
    return out


def _quantile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    idx = min(max(int(q * (len(ordered) - 1)), 0), len(ordered) - 1)
    return ordered[idx]


def _rolling(op: str, panel: Panel, window: int) -> Panel:
    dates = sorted(panel)
    history: dict[str, list[tuple[datetime, float]]] = {}
    out: Panel = {}
    for ts in dates:
        for name, value in panel[ts].items():
            history.setdefault(name, []).append((ts, value))
        row: dict[str, float] = {}
        for name, series in history.items():
            vals = [point[1] for point in series[-window:]]
            mapped = _rolling_value(op, vals, window)
            if mapped is not None:
                row[name] = mapped
        if row:
            out[ts] = row
    return out


def _rolling_value(op: str, vals: list[float], window: int) -> float | None:
    if op == "lag":
        if len(vals) < window:
            return None
        return vals[-window]
    if len(vals) < window:
        return None
    if op == "rolling_mean":
        return sum(vals) / len(vals)
    if op == "rolling_sum":
        return sum(vals)
    if op == "rolling_std":
        mean = sum(vals) / len(vals)
        var = sum((v - mean) ** 2 for v in vals) / len(vals)
        return math.sqrt(var)
    if op == "change":
        return vals[-1] - vals[0]
    if op == "ewma":
        alpha = 2.0 / (window + 1.0)
        acc = vals[0]
        for value in vals[1:]:
            acc = alpha * value + (1.0 - alpha) * acc
        return acc
    raise DiscoveryError(f"unknown rolling {op}")
