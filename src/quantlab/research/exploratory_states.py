"""Trailing state observables on an already timestamp-aligned exploratory frame.

Unlike a general revision-aware PIT query, this frame has one frozen print per
time/security. Compute once from that exact matrix rather than repeatedly sorting
every history prefix. Classification still uses the existing versioned detectors.
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np

from quantlab.domain.research import CheckResult
from quantlab.regimes.snapshot import StateSnapshot
from quantlab.research.exploratory import ExploratoryFrame


def exploratory_state_panel(
    frame: ExploratoryFrame,
    *,
    lookback: int,
    cancelled: Callable[[], None],
) -> list[StateSnapshot]:
    prices = np.asarray(
        [[bar.close for bar in rows] for rows in frame.bars.values()], dtype=float
    ).T
    returns = prices[1:] / prices[:-1] - 1.0
    mean_returns = returns.mean(axis=1)
    n_names = prices.shape[1]
    wealth = peak = 1.0
    worst_drawdown: float | None = None
    previous_vol: float | None = None
    out: list[StateSnapshot] = []
    for index, as_of in enumerate(frame.dates):
        cancelled()
        window = mean_returns[max(0, index - lookback) : index]
        market_return = float(mean_returns[index - 1]) if index else None
        vol = float(np.std(window, ddof=0)) if len(window) >= 2 else None
        trail = float(window.sum()) if len(window) >= lookback else None
        dispersion = float(np.std(returns[index - 1], ddof=0)) if index and n_names >= 2 else None
        breadth = float(np.mean(returns[index - 1] > 0)) if index and n_names >= 2 else None
        correlation: float | None = None
        if index >= lookback and lookback >= 5 and n_names >= 3:
            sample = returns[index - lookback : index]
            if np.all(np.std(sample, axis=0) > 0):
                corr = np.corrcoef(sample, rowvar=False)
                if np.isfinite(corr).all():
                    correlation = float((corr.sum() - np.trace(corr)) / (n_names * (n_names - 1)))
        if market_return is not None:
            wealth *= 1 + market_return
            peak = max(peak, wealth)
            drawdown = wealth / peak - 1
            worst_drawdown = drawdown if worst_drawdown is None else min(worst_drawdown, drawdown)
        velocity = None if vol is None or previous_vol is None else vol - previous_vol
        if vol is not None:
            previous_vol = vol
        fields = {
            "market_ew_return": market_return,
            "market_ew_return_20": trail,
            "realized_vol_20": vol,
            "dispersion_cs": dispersion,
            "breadth_sign": breadth,
            "avg_pairwise_corr": correlation,
            "ew_drawdown": worst_drawdown,
            "vol_velocity": velocity,
        }
        out.append(
            StateSnapshot.model_validate(
                {
                    "as_of": as_of,
                    "n_names": n_names,
                    **fields,
                    "missing": [
                        "index_nifty_return",
                        "liquidity_adv",
                        *[k for k, v in fields.items() if v is None],
                    ],
                    "status": CheckResult.WARN,
                    "note": (
                        "Selected-asset trailing state; "
                        "cross-sectional dispersion/breadth/correlation "
                        "unavailable."
                        if n_names == 1
                        else "Equal-weight selected-universe trailing state; "
                        "not NIFTY or a historical-membership-verified index."
                    )
                    + " Interval-close timing assumed; historical availability NOT_TESTED.",
                }
            )
        )
    return out
