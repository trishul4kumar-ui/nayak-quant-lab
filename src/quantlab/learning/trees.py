"""Shallow CART ensembles. Complexity is an identity field, not AutoML."""

from __future__ import annotations

from pydantic import BaseModel

from quantlab.core.errors import ModelError


class FittedTree(BaseModel):
    feature: int | None = None
    threshold: float = 0.0
    value: float = 0.0
    left: FittedTree | None = None
    right: FittedTree | None = None


def fit_tree(
    x_rows: list[list[float]],
    y: list[float],
    *,
    max_depth: int,
    min_leaf: int,
    rng: list[int],
    max_features: int | None = None,
) -> FittedTree:
    if not x_rows:
        raise ModelError("insufficient_history")
    return _split(
        x_rows,
        y,
        depth=0,
        max_depth=max_depth,
        min_leaf=min_leaf,
        rng=rng,
        max_features=max_features,
    )


def predict_tree(tree: FittedTree, x_rows: list[list[float]]) -> list[float]:
    return [_walk(tree, row) for row in x_rows]


def fit_forest(
    x_rows: list[list[float]],
    y: list[float],
    *,
    n_estimators: int,
    max_depth: int,
    min_leaf: int,
    seed: int,
) -> list[FittedTree]:
    p = len(x_rows[0])
    max_features = max(1, int(p**0.5))
    rng = [seed]
    trees: list[FittedTree] = []
    n = len(x_rows)
    for _ in range(n_estimators):
        idx = [_rand_below(rng, n) for _ in range(n)]
        bx = [x_rows[i] for i in idx]
        by = [y[i] for i in idx]
        trees.append(
            fit_tree(
                bx,
                by,
                max_depth=max_depth,
                min_leaf=min_leaf,
                rng=rng,
                max_features=max_features,
            )
        )
    return trees


def predict_forest(trees: list[FittedTree], x_rows: list[list[float]]) -> list[float]:
    if not trees:
        return [0.0] * len(x_rows)
    acc = [0.0] * len(x_rows)
    for tree in trees:
        pred = predict_tree(tree, x_rows)
        for i, value in enumerate(pred):
            acc[i] += value
    k = float(len(trees))
    return [v / k for v in acc]


def fit_boosting(
    x_rows: list[list[float]],
    y: list[float],
    *,
    n_estimators: int,
    max_depth: int,
    min_leaf: int,
    learning_rate: float,
    seed: int,
) -> tuple[float, list[FittedTree]]:
    rng = [seed]
    init = sum(y) / len(y)
    pred = [init] * len(y)
    trees: list[FittedTree] = []
    for _ in range(n_estimators):
        resid = [y[i] - pred[i] for i in range(len(y))]
        tree = fit_tree(
            x_rows,
            resid,
            max_depth=max_depth,
            min_leaf=min_leaf,
            rng=rng,
            max_features=len(x_rows[0]),
        )
        step = predict_tree(tree, x_rows)
        pred = [pred[i] + learning_rate * step[i] for i in range(len(pred))]
        trees.append(tree)
    return init, trees


def predict_boosting(
    init: float, trees: list[FittedTree], learning_rate: float, x_rows: list[list[float]]
) -> list[float]:
    pred = [init] * len(x_rows)
    for tree in trees:
        step = predict_tree(tree, x_rows)
        pred = [pred[i] + learning_rate * step[i] for i in range(len(pred))]
    return pred


def _split(
    x_rows: list[list[float]],
    y: list[float],
    *,
    depth: int,
    max_depth: int,
    min_leaf: int,
    rng: list[int],
    max_features: int | None,
) -> FittedTree:
    leaf = FittedTree(value=sum(y) / len(y))
    if depth >= max_depth or len(y) < 2 * min_leaf:
        return leaf
    p = len(x_rows[0])
    features = list(range(p))
    if max_features is not None and max_features < p:
        features = _sample(features, max_features, rng)
    best_sse = _sse(y)
    best: tuple[int, float, list[int], list[int]] | None = None
    for j in features:
        ordered = sorted({row[j] for row in x_rows})
        for k in range(len(ordered) - 1):
            thresh = 0.5 * (ordered[k] + ordered[k + 1])
            left_i = [i for i, row in enumerate(x_rows) if row[j] <= thresh]
            right_i = [i for i in range(len(x_rows)) if i not in set(left_i)]
            if len(left_i) < min_leaf or len(right_i) < min_leaf:
                continue
            sse = _sse([y[i] for i in left_i]) + _sse([y[i] for i in right_i])
            if sse < best_sse:
                best_sse = sse
                best = (j, thresh, left_i, right_i)
    if best is None:
        return leaf
    j, thresh, left_i, right_i = best
    left = _split(
        [x_rows[i] for i in left_i],
        [y[i] for i in left_i],
        depth=depth + 1,
        max_depth=max_depth,
        min_leaf=min_leaf,
        rng=rng,
        max_features=max_features,
    )
    right = _split(
        [x_rows[i] for i in right_i],
        [y[i] for i in right_i],
        depth=depth + 1,
        max_depth=max_depth,
        min_leaf=min_leaf,
        rng=rng,
        max_features=max_features,
    )
    return FittedTree(feature=j, threshold=thresh, value=leaf.value, left=left, right=right)


def _walk(tree: FittedTree, row: list[float]) -> float:
    if tree.feature is None or tree.left is None or tree.right is None:
        return tree.value
    if row[tree.feature] <= tree.threshold:
        return _walk(tree.left, row)
    return _walk(tree.right, row)


def _sse(values: list[float]) -> float:
    mu = sum(values) / len(values)
    return sum((v - mu) ** 2 for v in values)


def _rand_below(rng: list[int], n: int) -> int:
    rng[0] = (1103515245 * rng[0] + 12345) % (2**31)
    return rng[0] % n


def _sample(items: list[int], k: int, rng: list[int]) -> list[int]:
    pool = list(items)
    out: list[int] = []
    for _ in range(min(k, len(pool))):
        idx = _rand_below(rng, len(pool))
        out.append(pool.pop(idx))
    return out
