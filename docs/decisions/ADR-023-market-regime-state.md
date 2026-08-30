# ADR-023 — Market regime, state, and temporal dynamics

## Context
Prompt 09 asks what the observable market state was at T, how it evolved, which regimes can be identified without hindsight, and how alpha, factor, risk, and portfolio objects behave conditional on that state. Prompts 01–08 already own the PIT fabric, feature/alpha engines, portfolio constructors, factor/risk research, next-bar backtester, firewall, ledger, and research gate.

Per-instrument `quantlab.domain.models.MarketState` (ADR-010) already exists as the name-level as-of object.

## Problem
A second MarketState type, an invented NIFTY series, filling missing state with zero, treating HMM smoothing as a trading feature, or folding regime labels into alpha would leak the future and confuse description with forecast.

## Options
1. Replace ADR-010 MarketState with a cross-sectional regime object
2. Add `quantlab.regimes` with `StateSnapshot` (market-level) beside existing per-instrument MarketState; keep detectors versioned and PIT
3. Fabricate NIFTY / ADV / holidays so every state variable looks implemented

## Decision
Option 2.

```
FEATURE ≠ MARKET STATE ≠ REGIME ≠ REGIME FORECAST ≠ ALPHA
REGIME DETECTION ≠ REGIME FORECASTING
FILTERED ≠ SMOOTHED
```

- `StateSnapshot` is the cross-section observable at T (`quantlab.regimes.snapshot`). ADR-010 `MarketState` is unchanged.
- Market proxy remains `equal_weight_universe`. Do not label it NIFTY.
- Missing state is `None`, never silent 0. NIFTY return and calibrated ADV stay `NOT_TESTED`.
- HMM smoothing and full-sample clustering raise `RegimeError` when `predictive=True`.
- Change-point flags are not regime labels (`detect_changes`, not `classify`).
- `regimes/__init__.py` stays thin: no import of `experiment` or `research.suite`.
- Desktop Market page is a `quantlab.app` query viewer; it does not fit HMM.
- Prompt 05 remains the only promotion gate; synthetic cannot promote.
- Prompt 05 `research.robustness.regime_slices` remains an equity-curve median split of a backtest, not this detector.

## Consequences
- Rule-based vol/trend/correlation buckets are the baseline.
- Filtered HMM and walk-forward clustering may be used as historical descriptions with information through T.
- Smoothed HMM / full-sample clusters are retrospective research only.
- Integrity grows `future_regime`, `hmm_smoothing`, and `full_sample_regime_fit`.

## References
Prompt 09; ADR-010; ADR-019; ADR-020; ADR-021; ADR-022
