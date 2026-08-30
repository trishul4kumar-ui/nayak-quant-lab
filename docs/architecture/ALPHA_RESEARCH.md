# Alpha research

An alpha is a versioned, hypothesis-bound transformation of features. Example:

- Feature: `momentum_20 = close[t]/close[t-20]-1`
- Alpha: `rank(momentum_20)` or `zscore(momentum_20)-zscore(rolling_std_20)`
- Strategy: top-N long-only mapping of that alpha
- Portfolio: firewall-approved target weights

## Combinations

Equal-weight standardized, weighted standardized, rank average, rank sum, linear combo. Weights are explicit. There is no test-set weight optimizer.

Orthogonalization is contemporaneous cross-sectional OLS of one feature on another (linear, intercept included). A full factor library is `NOT_TESTED`.

## Expression model

The genome AST gained `add`, `sub`, and `scale`. Unrestricted Python `eval` is forbidden. Existing `rank(zscore(feature))` genomes still evaluate.

## Gate

Prompt 05 remains the promotion gate. Feature IC experiments record `n_hypotheses_in_family` and `selection_stage` for FDR/DSR. Synthetic data cannot become `RESEARCH_CANDIDATE`. Max outcome in this phase is still `RESEARCH_CANDIDATE` via that gate. There is no LIVE path.
