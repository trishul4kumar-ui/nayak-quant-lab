# ADR-036 — Econometric & Causal Research Engine

## Context
Prompt 22 asks whether an observed relationship remains statistically credible after dependence, non-stationarity, breaks, confounding, regimes, and multiple testing — without a second backtester, PIT fabric, covariance engine, FDR engine, or research gate.

## Decision
Add `quantlab.econometrics` as a research diagnostic engine. ADF/KPSS are numpy-only; Phillips-Perron and Johansen stay explicit `NOT_TESTED` interfaces. Granger is labelled **predictive**, never causation. Lag selection uses the training window only. Prompt 05 remains the gate; Prompt 14 `evaluate_family` remains the family accountant.

## Consequences
- Synthetic series are architecture diagnostics, not NSE evidence
- Small samples return `NOT_TESTED`, not invented p-values
- `LIVE_TRADING` remains false
- Econometrics Lab is a new nav key (`econo`); it does not reuse Prompt 05 Validation
