# ADR-025 — Statistical learning and model research

## Context
Prompt 11 asks whether a statistical model extracts incremental, persistent, economically meaningful information from PIT-valid features and alphas, beyond simpler baselines, while surviving temporal validation, costs, risk, multiple testing, and selection bias. Prompts 01–10 already own the PIT fabric, feature/alpha/portfolio/factor/risk/regime/adaptive engines, next-bar backtester, firewall, ledger, and research gate. `quantlab.models` already holds the experiment ledger, so the engine lives in `quantlab.learning`.

## Problem
Fitting on the full sample then replaying history, selecting features or PCA on the holdout, treating a tree as alpha, or promoting synthetic R² would collapse research into a demo.

## Options
1. Add scikit-learn as a required AutoML surface and fit models in the desktop
2. Add `quantlab.learning` with numpy estimators, walk-forward predict-then-realize, baselines first, Prompt 05 as the only gate
3. Put fitted models inside `quantlab.models` next to the ledger

## Decision
Option 2.

```
DATA ≠ FEATURE ≠ FACTOR ≠ ALPHA ≠ REGIME ≠ MODEL ≠ ADAPTIVE LEARNER ≠ PORTFOLIO ≠ ORDER
TRAIN → FREEZE → PREDICT → REALIZE → UPDATE
MODEL ≠ ALPHA
```

- Model output is a research-time score. It is not an order.
- Existing backtester remains canonical for portfolio simulation.
- Scaling, selection, and PCA fit only on the training window for predictive claims.
- Complex models require a baseline comparison. Incremental information is required.
- Adaptive learning remains Prompt 10. Regime context remains Prompt 09. Risk remains Prompt 08.
- Prompt 05 remains the only promotion gate. Synthetic cannot promote.
- Desktop Model Lab is a `quantlab.app` query viewer.
- `LIVE_TRADING` remains false. No broker imports in learning code. No sklearn dependency.

## Consequences
- Walk-forward IC/RMSE is the online score; Prompt 05 still gates promotion.
- Full-sample replay, future PCA, future selection, future hyperparameters, and label-as-feature FAIL integrity.
- `SIMPLE MODEL > COMPLEX MODEL` and `NO INCREMENTAL INFORMATION` are valid results.

## References
Prompt 11; ADR-019 through ADR-024
