# ADR-026 — Advanced ensemble, meta-alpha, and model combination

## Context
Prompt 12 asks whether multiple imperfect, partially independent sources can be combined into a more robust score without ensemble-selection, stacking, weighting, or temporal leakage. Prompts 01–11 already own the PIT fabric, feature/alpha/portfolio/factor/risk/regime/adaptive/learning engines, next-bar backtester, firewall, ledger, and research gate. Prompt 07 already defines `AlphaEnsemble` in `quantlab.alpha.ensemble` and `quantlab research ensemble`.

## Problem
Fitting weights on future IC, stacking on in-sample base predictions, searching the holdout, silently relaxing constraints, or treating a combination as a portfolio/order would collapse research into a demo.

## Options
1. Extend Prompt 07 `AlphaEnsemble` and steal `research ensemble`
2. Add `quantlab.ensemble` with versioned combination objects, PIT weighting/stacking, equal-weight and best-component baselines, Prompt 05 as the only gate
3. Add a second backtester that optimizes ensemble Sharpe

## Decision
Option 2.

```
DATA ≠ FEATURE ≠ FACTOR ≠ ALPHA ≠ REGIME ≠ MODEL ≠ ADAPTIVE LEARNER ≠ ENSEMBLE ≠ META-ALPHA ≠ PORTFOLIO ≠ ORDER
ENSEMBLE ≠ PORTFOLIO
META-ALPHA ≠ ALPHA
```

1. Ensembles are research objects. Output is a research-time score, not an order.
2. Meta-alpha is distinct from alpha. Component lineage is retained.
3. Components remain independently versioned (ALPHA / MODEL / ADAPTIVE / FACTOR).
4. PIT is mandatory for scores, IC, correlation, covariance, weights, pruning, and meta-features.
5. Prompt 11 learning infrastructure is reused for linear meta-alpha and stacking.
6. Prompt 08 covariance/risk infrastructure is reused (diagonal shrinkage formula). No second asset-cov engine.
7. Stacking requires temporally valid out-of-sample base predictions.
8. Ensemble selection is subject to multiple-testing controls. Failed candidates are retained.
9. Equal-weight (`w_i = 1/N`) is a mandatory baseline, as is best individual component.
10. Marginal contribution (leave-one-out ΔIC) is mandatory.
11. Dynamic weights require PIT evidence. Sign is not flipped from future IC unless an explicit Prompt 10 policy says so.
12. Prompt 05 remains the sole research gate.
13. Synthetic results cannot promote.
14. No broker integration. `quantlab research ensemble` remains Prompt 07.
15. `LIVE_TRADING` remains false.

Desktop Ensemble Lab is a `quantlab.app` query viewer. It does not fit ensembles.

## Consequences
- Combination IC/RankIC is the information-layer score; portfolio P&L still uses the existing backtester.
- Future weights, future correlation, stacking leaks, and holdout search FAIL integrity.
- `ensemble adds no information` and `components are redundant` are successful research outcomes.

## References
Prompt 12; ADR-019 through ADR-025
