# Econometric Research Engine

**Version:** 2.3.0  
**Package:** `quantlab.econometrics`  
**ADR:** [ADR-036](../decisions/ADR-036-econometric-research-engine.md)

`quantlab.econometrics` tests whether a relationship survives dependence, non-stationarity, breaks, and multiple testing. It is not a second backtester, PIT fabric, covariance engine, FDR engine, or gate.

```text
DATA ≠ FEATURE ≠ FACTOR ≠ ALPHA ≠ REGIME ≠ MODEL ≠ CAUSAL HYPOTHESIS
≠ ECONOMETRIC ESTIMATE ≠ STATISTICAL SIGNIFICANCE ≠ ECONOMIC SIGNIFICANCE
≠ PORTFOLIO ≠ ORDER
CORRELATION ≠ CAUSATION
P-VALUE ≠ ECONOMIC VALUE
IN-SAMPLE FIT ≠ OOS EVIDENCE
```

CLI: `quantlab econometrics stationarity|dependence|cointegration|var|vecm|granger|breaks|panel|causal|report`

Desktop: **Econometrics Lab** (`econo`). Qt does not fit models.
