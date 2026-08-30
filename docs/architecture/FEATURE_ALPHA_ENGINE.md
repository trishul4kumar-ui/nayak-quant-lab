# Feature & Alpha Research Engine

**Status:** Prompt 06 (2026-08-30) — ADR-020  
**Packages:** `quantlab.features`, `quantlab.labels`, `quantlab.alpha`

## Question

Does a point-in-time-valid, economically meaningful relationship exist between information available at T and subsequent behavior? This is not an indicator library.

## Distinctions

| Object | Meaning |
|---|---|
| Feature | Trailing function of PIT-available data |
| Label | Forward quantity known only after T |
| Alpha | Hypothesis-bound transformation of features |
| Strategy | Portfolio mapping of an alpha |
| Portfolio | Target weights after the firewall |

A feature with no IC is a valid research result. Strong IC cannot promote; Prompt 05’s gate remains authoritative. Synthetic IC is architecture evidence, not market evidence.

## Dependency direction

```
data → features / labels → alpha → research / validation / backtest → app → ui
```

`features` and `labels` must not import `research.suite` or `backtest.engine`. `research/__init__.py` stays thin.

## Identity

`FeatureDefinition.identity_hash()` covers formula, inputs, lookback, operator, normalization, missing policy, winsorization, price field, and version. A formula change requires a new version. The registry refuses overwrite.

## Seed library

Trailing returns 1/5/10/20/60/120/252 (same `close[t]/close[t-N]-1` as `MarketState`), rolling mean/std, trailing z-score, range, volume diagnostics, cross-sectional ranks. Rolling beta, sector, market-cap, and ADV buckets exist as definitions and stay `NOT_TESTED`.

## Labels

`ForwardReturn(H)`, `ForwardVolatility(H)`, `ForwardDrawdown(H)`, `ForwardBinaryDirection(H)`. `ForwardExcessReturn` is `NOT_TESTED` without a PIT benchmark (NIFTY is not invented). Labels never enter feature computation.

## Desktop

Features, Alpha Lab, and Portfolio Lab are viewers of `quantlab.app` queries. They do not compute features or weights, bypass PIT, rewrite the ledger, or promote alpha.
