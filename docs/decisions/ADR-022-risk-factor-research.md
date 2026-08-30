# ADR-022 — Quantitative risk and factor research engine

## Context
Prompt 08 asks what risks sit in an alpha or portfolio, where they come from, how stable they are, and whether apparent alpha survives systematic controls. Prompts 01–07 already own the PIT fabric, feature/alpha engines, portfolio constructors, next-bar backtester, firewall, ledger, and research gate.

## Problem
A second covariance engine, an invented NIFTY series, filling missing betas with zero, or folding the optimizer into `quantlab.risk` would fork Prompt 07 semantics and smuggle alpha into the risk model.

## Options
1. Replace the firewall with a Barras-style commercial factor model
2. Add `quantlab.factors` and extend `quantlab.risk` / `portfolio.covariance` without a second Σ or a second backtester
3. Fabricate cap/fundamentals/sector/index so every style factor looks implemented

## Decision
Option 2.

- `FEATURE ≠ FACTOR ≠ ALPHA ≠ RISK MODEL ≠ PORTFOLIO`
- Risk model ≠ alpha model: future returns never enter Σ or B
- Market proxy is `equal_weight_universe`, documented as not an official index
- Size/value/quality/liquidity/sector: definitions exist, `FactorSource.NOT_IMPLEMENTED`
- Missing exposure is `None`, never silent 0; hard `max_beta` / `max_factor_exposure` without a value is `InfeasiblePortfolio`
- Residualized factors get a new identity
- Stress scenarios are not forecasts; OLS intercept is a model estimate
- `risk/__init__.py` stays firewall-only; `factors/__init__.py` does not import experiment
- Desktop Risk Lab is a `quantlab.app` query viewer
- Prompt 05 remains the only promotion gate; synthetic cannot promote

## Consequences
- EW-universe beta is testable; NIFTY beta stays `NOT_TESTED`
- Covariance estimators (sample, EWMA, shrinkage) share one PIT implementation
- Portfolio construction may consume exposures; it does not import `risk.experiment`

## References
Prompt 08; ADR-006; ADR-019; ADR-020; ADR-021
