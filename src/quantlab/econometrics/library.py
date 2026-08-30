"""Synthetic diagnostic series. Never labelled as NSE evidence."""

from __future__ import annotations

import numpy as np


def stationary_ar1(*, n: int, seed: int, phi: float = 0.4) -> list[float]:
    rng = np.random.default_rng(seed)
    values = np.zeros(n, dtype=np.float64)
    shock = rng.normal(0.0, 1.0, size=n)
    for i in range(1, n):
        values[i] = phi * values[i - 1] + shock[i]
    return values.tolist()


def random_walk(*, n: int, seed: int) -> list[float]:
    rng = np.random.default_rng(seed)
    return np.cumsum(rng.normal(0.0, 1.0, size=n)).tolist()


def cointegrated_pair(*, n: int, seed: int) -> tuple[list[float], list[float]]:
    common = random_walk(n=n, seed=seed)
    noise = stationary_ar1(n=n, seed=seed + 1, phi=0.2)
    y = [a + 0.2 * b for a, b in zip(common, noise, strict=True)]
    x = list(common)
    return y, x


def panel_toy(
    *, n_entity: int, n_time: int, seed: int
) -> tuple[list[float], list[float], list[str], list[str]]:
    rng = np.random.default_rng(seed)
    y: list[float] = []
    x: list[float] = []
    entity: list[str] = []
    time_id: list[str] = []
    for e in range(n_entity):
        for t in range(n_time):
            xi = float(rng.normal())
            y.append(0.5 * xi + 0.1 * e + float(rng.normal() * 0.2))
            x.append(xi)
            entity.append(f"E{e}")
            time_id.append(f"T{t}")
    return y, x, entity, time_id
