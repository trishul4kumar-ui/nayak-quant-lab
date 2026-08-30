# Regime engine

**Status:** Prompt 09 (2026-08-30) — ADR-023  
**Package:** `quantlab.regimes`

A regime label is a description of observable state. It is not a forecast and not alpha.

```
FEATURE ≠ MARKET STATE ≠ REGIME ≠ REGIME FORECAST ≠ ALPHA
FILTERED ≠ SMOOTHED
```

Prompt 05 remains the promotion gate. Synthetic regime detection is not evidence of tradable market regimes.

## Detectors

| Seed | Kind | Predictive? |
|---|---|---|
| `vol_tercile`, `trend_sign`, `vol_trend`, `corr_tercile` | Rule (expanding buckets / sign) | Yes — window ends at T |
| `hmm_vol_filter` | 1-D Gaussian HMM, filtered (Viterbi on prefix through T) | Yes |
| `hmm_vol_smooth` | Full-sample forward–backward | No — `RegimeError` if `predictive=True` |
| `cluster_vol_wf` | Walk-forward 2-means | Yes |
| `cluster_vol_full` | Full-sample 2-means | No — `RegimeError` if `predictive=True` |
| `cusum_ew` | CUSUM flags on EW returns | Not a regime; use `detect_changes` |

Hard labels and probabilities are separate fields on `RegimeObservation`. HMM state names are anonymous (`state_0`, `state_1`).

## Transitions and duration

Empirical `P(R_{t+1}=j | R_t=i)` from consecutive hard labels. Rows are probabilities (empty from-rows are treated as stay). Run lengths are not a forecast of remaining time in regime.

## Temporal diagnostics

Velocity, acceleration, lag-1 autocorrelation, half-sample mean-shift, Mahalanobis of the last expanding-z vector (`inv`, not `pinv`), analog k-NN. ADF unit-root tests are `NOT_TESTED` (no bundled library).

## Conditional research

`conditional_ic` and `conditional_covariance` slice existing factor/label panels and `Σ(T)` by contemporaneous regime. Association is not causation. Thin slices stay `NOT_TESTED`.

## Identity and cache

`RegimeModel.identity_hash()` covers detector, features, lookback, parameters, labels, and version. The registry refuses overwrite. Cache keys include identity, snapshot, universe, window, and seed.

`regimes/__init__.py` does not import `experiment`.

`quantlab regime list|inspect|fit|classify|transitions|durations|changes`
