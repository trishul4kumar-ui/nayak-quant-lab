# Factor Engine

**Status:** Prompt 08 (2026-08-30) — ADR-022  
**Package:** `quantlab.factors`

A factor is a systematic characteristic. It is not a feature, not an alpha, and not a risk model.

## Distinctions

| Object | Meaning |
|---|---|
| Feature | Trailing PIT function of available data |
| Factor | Cross-sectional risk characteristic (exposure) |
| Alpha | Hypothesis-bound transformation of features |
| Risk model | Variance / covariance / exposure description |
| Portfolio | Target weights after construction and the firewall |

A high factor IC is not automatic alpha. Residual variance is not automatic alpha. Prompt 05 remains the promotion gate.

## PIT

`factor(T)` uses `available_time <= T` and `Universe(T)`. Appending later bars cannot change the value at T. Missing values are `NOT_AVAILABLE`, never silent zeros.

## Seed library

Implemented from bundled bars:

- `market_ew_beta` — beta vs the **equal-weight universe** (CS mean of PIT simple returns). Not NIFTY.
- `style_momentum_20`, `style_reversal_5`, `style_volatility_20` — style exposures from existing features

Definitions exist, lifecycle `NOT_TESTED`, source `NOT_IMPLEMENTED`:

- `size_log_cap`, `value_book_to_market`, `quality_roe`, `liquidity_adv`, `sector_membership`

The lab does not invent market cap, book equity, ADV, or a historical sector map.

## Identity

`FactorDefinition.identity_hash()` covers formula, inputs, lookback, source, feature_id, normalization, missing policy, winsorization, direction, frequency, and version. The registry refuses overwrite. Residualizing a factor creates a **new** identity; the original is not mutated.

## Engine

`compute_factor_panel` wraps the feature engine or rolling EW-universe beta. Residual factors must be computed via `residualize_panel`. NaN/Inf fail closed (`AlignmentError`).

`factors/__init__.py` stays thin: it does not import `experiment` or `research.suite`.
