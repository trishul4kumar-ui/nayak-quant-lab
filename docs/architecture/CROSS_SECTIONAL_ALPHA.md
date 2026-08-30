# Cross-sectional alpha

**Status:** Prompt 07 (2026-08-30) — ADR-021  
**Package:** `quantlab.alpha.ensemble`

An alpha is a hypothesis-bound transformation of features. An ensemble is a **versioned, explicit** combination of alphas. It is not a portfolio and not a search over test-set weights.

```
Feature → Alpha → Ensemble scores → Portfolio constructor → Firewall → existing next-bar engine
```

## Sign

`expected_direction` `long_high` keeps scores. `long_low` / `-1` multiplies by −1. The lab never flips sign because in-sample Sharpe looks better.

## Missing names

Default `exclude`: intersection of names with a finite score. `neutralize` z-scores the cross-section first, then fills missing names with **explicit** 0. Raw missing is never silently treated as 0.

## Combiners

`equal_weight`, `fixed_weights`, `rank_average`, `zscore_average`, `weighted_rank`. Component weights are part of ensemble identity. Changing a weight requires a new version.

## Gate

Ensemble IC is a diagnostic. Promotion still goes through Prompt 05. Synthetic ensemble IC cannot become `RESEARCH_CANDIDATE`.
