# QUANT LAB PROMPT 22
## Advanced Time-Series, Econometric & Causal Market Research Engine
### Institutional Research Specification — Build on QUANT LAB 2.1.0

**Cursor directive:** Implement this on the existing QUANT LAB repository. Do not reset, rewrite, fork, or duplicate Prompts 01–21. First inspect the complete architecture, ADRs, tests, package boundaries, CLI, `quantlab.app`, UI, integrity framework, knowledge graph, experiment ledger, and safety gates.

## Mission

Build an institutional-grade econometric research engine answering:

> Does an observed market relationship remain statistically credible after temporal dependence, non-stationarity, structural breaks, confounding, regime dependence, and multiple testing are considered?

This is research infrastructure only. It must never place orders, modify portfolios, bypass Prompt 05, create another backtester/PIT fabric/FDR engine, or manufacture significance.

## Mandatory separation

```text
DATA ≠ FEATURE ≠ FACTOR ≠ ALPHA ≠ REGIME ≠ MODEL
≠ CAUSAL HYPOTHESIS ≠ ECONOMETRIC ESTIMATE
≠ STATISTICAL SIGNIFICANCE ≠ ECONOMIC SIGNIFICANCE
≠ PORTFOLIO ≠ ORDER
```

`CORRELATION ≠ CAUSATION`, `P-VALUE ≠ ECONOMIC VALUE`, and `IN-SAMPLE FIT ≠ OOS EVIDENCE`.

## Architecture

Create a thin `quantlab.econometrics` package. Reuse existing Prompt 04 PIT data, Prompt 05 validation/gate, Prompt 06 features/labels, Prompt 08 risk/covariance, Prompt 09 regimes, Prompt 10 chronology, Prompt 11 learning, Prompt 14 orchestration/multiple testing, Prompt 16 knowledge, Prompt 19 monitoring, Prompt 20 production data, Prompt 21 TCA, and the existing ledger.

Never create a second data fabric, backtester, covariance engine, FDR engine, or gate.

Every run must bind to and hash:

```text
dataset/snapshot
as_of/range
universe
feature/label identities
transforms
specification
estimator
lags/hyperparameters
diagnostic policy
seed
software version
```

## Required research capabilities

Implement dependency-light, versioned research objects and diagnostics for:

1. **Stationarity:** ADF, KPSS, PP interface where supported, transformations, rolling diagnostics.
2. **Dependence:** ACF/PACF, Ljung–Box, HAC/Newey-West, heteroskedasticity diagnostics, dependence-aware residual analysis.
3. **Cointegration:** Engle-Granger, residual diagnostics, error-correction representation, Johansen interface where justified, rolling stability.
4. **VAR/VECM:** lag selection using training windows only, VAR, VECM, impulse response, forecast-error variance decomposition.
5. **Granger predictive causality:** pairwise/multivariate where appropriate, lag sensitivity, rolling tests, temporal block/permutation falsification. Never call this proof of causation.
6. **Structural breaks:** CUSUM, rolling coefficient stability, known-break tests where valid, breakpoint research, parameter drift, regime-conditioned estimates.
7. **Panel/cross-sectional econometrics:** pooled regression, entity/time/two-way fixed effects, clustered errors, Fama-MacBeth-style research, residual analysis.
8. **Causal research:** immutable `CausalHypothesis` and `CausalSpecification`; support DiD, event studies, synthetic-control-style interfaces, placebo tests, pre-trend diagnostics where assumptions are explicit.
9. **Robust inference:** HAC, moving/block bootstrap, sign-flip/permutation methods appropriate to temporal dependence, clustered inference, confidence/effect-size intervals.
10. **Economic significance:** separate statistical result, economic effect, execution-adjusted effect, robustness, and limitations. Reuse Prompt 13/21 execution assumptions.

Small samples or unsupported assumptions must produce `NOT_TESTED`, never invented statistics.

## Temporal integrity

Add explicit checks including:

```text
future_stationarity_window
future_lag_selection
future_break_detection
future_cointegration_selection
future_var_selection
future_causal_control
future_event_window
future_parameter_estimation
full_sample_econometric_replay
future_residual_normalization
future_panel_selection
causal_post_treatment_control
lookahead_event_study
```

Semantics:

```text
None → NOT_TESTED
validated → PASS
proven leak → FAIL
```

Never downgrade FAIL silently.

## Econometric identities

Implement immutable/versioned:

```text
EconometricSpecification
StationarityTest
DependenceDiagnostic
CointegrationTest
VARSpecification
VECMSpecification
CausalityTest
StructuralBreakTest
PanelSpecification
CausalSpecification
EconometricResult
EconometricDiagnostics
```

Formula/specification changes require a new identity.

## Multiple testing

Reuse Prompt 14's canonical family/FDR implementation. Record family ID, tested count, search space, selection policy, and correction method. Exploratory search must never be presented as preregistered confirmation.

## Knowledge integration

Write successful, failed, contradictory, and inconclusive findings to Prompt 16. Preserve failed hypotheses and structural-break findings. Never delete research history.

## CLI

Add:

```text
quantlab econometrics list
quantlab econometrics inspect <id>
quantlab econometrics stationarity <feature>
quantlab econometrics dependence <feature>
quantlab econometrics cointegration <a> <b>
quantlab econometrics var <spec>
quantlab econometrics vecm <spec>
quantlab econometrics granger <x> <y>
quantlab econometrics breaks <spec>
quantlab econometrics panel <spec>
quantlab econometrics causal <spec>
quantlab econometrics residuals <experiment>
quantlab econometrics robustness <experiment>
quantlab econometrics report <experiment>
```

Research aliases:

```text
quantlab research econometrics
quantlab research stationarity
quantlab research granger
quantlab research cointegration
quantlab research structural-break
quantlab research causal
quantlab research panel
```

## Desktop

Add **Econometrics Lab** through `quantlab.app`. Qt is viewer-only: no direct Parquet/DuckDB access, fitting, causal estimation, ledger writes, or gate overrides.

## Safety

`LIVE_TRADING=false` must remain true. No Zerodha/Kite/OpenAlgo/broker imports. Econometrics may produce evidence; it may never produce an order.

## Synthetic policy

Synthetic results are architecture diagnostics, never market evidence and never eligible for research promotion/paper/live status.

## Testing

Create meaningful tests for PIT estimation, chronology, stationarity, dependence, HAC, cointegration, VAR/VECM, Granger, breaks, panel, causal guardrails, placebo/falsification, multiple-testing integration, determinism, hashing, knowledge lineage, synthetic gating, and UI smoke.

Target **≥80 dedicated econometrics tests** plus full regression.

## Documentation

Create:

```text
docs/architecture/ECONOMETRIC_RESEARCH_ENGINE.md
docs/research/TIME_SERIES_RESEARCH.md
docs/research/STATIONARITY.md
docs/research/COINTEGRATION.md
docs/research/VAR_VECM.md
docs/research/GRANGER_RESEARCH.md
docs/research/STRUCTURAL_BREAKS.md
docs/research/PANEL_ECONOMETRICS.md
docs/research/CAUSAL_RESEARCH.md
docs/research/ROBUST_INFERENCE.md
docs/decisions/ADR-036-econometric-research-engine.md
```

Update README, BACKLOG, LOCAL_RUN, architecture map, health, and version.

## Definition of done

```text
__version__ = 2.2.0
ruff clean on owned code
mypy --strict clean on owned code
≥80 dedicated econometrics tests
full regression passes
UI offscreen smoke passes
LIVE_TRADING=false
zero broker imports
PIT integrity verified
Prompt 14 multiple testing reused
existing backtester reused
knowledge lineage works
NOT_TESTED remains honest
synthetic cannot promote
```

**Final principle:** optimize the engine to make QUANT LAB harder to fool, not easier to produce positive results. A relationship that disappears under HAC, walk-forward analysis, structural-break testing, falsification, execution costs, or multiple-testing correction is a successful research finding.
