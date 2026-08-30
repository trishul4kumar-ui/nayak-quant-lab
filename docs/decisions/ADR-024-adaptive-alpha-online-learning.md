# ADR-024 — Adaptive alpha and online learning

## Context
Prompt 10 asks whether an alpha remains useful as the information distribution, market state, regime, and efficacy evolve, and whether research parameters can be adapted without hindsight, leakage, unstable behavior, or hidden multiple testing. Prompts 01–09 already own the PIT fabric, feature/alpha/portfolio/factor/risk/regime engines, next-bar backtester, firewall, ledger, and research gate.

## Problem
A second backtester, a live “online trader,” fitting on the full sample then replaying predictions, flipping sign from future IC, or promoting synthetic adaptive Sharpe would collapse research into a story.

## Options
1. Replace Prompt 06 alphas with an autonomous learner that places orders
2. Add `quantlab.adaptive` with prequential predict→realize→score→update, static baselines first, Prompt 05 as the only gate
3. Select half-lives and ensemble weights on the holdout and call it OOS

## Decision
Option 2.

```
FEATURE ≠ FACTOR ≠ ALPHA ≠ REGIME ≠ MODEL ≠ ONLINE LEARNER ≠ PORTFOLIO ≠ ORDER
FILTERED ≠ SMOOTHED
PREDICT THEN UPDATE
```

- Adaptive output is a research-time score or ensemble weight. It is not an order.
- Existing backtester remains canonical for portfolio simulation.
- PIT: outcomes available after T cannot affect the prediction at T.
- Static / rolling / expanding / EWMA / no-adaptation baselines are mandatory.
- Adaptive improvement is not alpha. Synthetic cannot promote.
- Desktop Adaptive Lab is a `quantlab.app` query viewer.
- `LIVE_TRADING` remains false. No broker imports in adaptive code.

## Consequences
- Prequential IC is the online score; Prompt 05 still gates promotion.
- Smoothed HMM / full-sample regimes raise if used as predictive context.
- Holdout-selected hyperparameters FAIL `holdout_contamination`.
- `ADAPTATION DOES NOT HELP` is a valid result.

## References
Prompt 10; ADR-019; ADR-020; ADR-021; ADR-022; ADR-023
