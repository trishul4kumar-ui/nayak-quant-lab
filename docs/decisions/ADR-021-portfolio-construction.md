# ADR-021 — Cross-sectional alpha ensembles and portfolio construction

## Context
Prompt 07 asks how multiple PIT-valid alphas become a constrained target portfolio without the optimizer inventing predictive power. Prompts 01–06 already own the fabric, next-bar engine, firewall, ledger, and research gate.

## Problem
A second backtester, a second ledger, or an optimizer that searches weights on the test set would fork fill/cost semantics and hide alpha selection inside a QP.

## Options
1. Replace `run_backtest` with a vectorized portfolio engine
2. Add `alpha.ensemble` + `portfolio.{spec,builder,constraints,covariance,experiment}` that emit target weights into the existing engine
3. Commercial QP + factor risk model in this phase

## Decision
Option 2.

- Ensemble identity is hashed; component weights are explicit
- Sign is `expected_direction`, never Sharpe-driven
- Hard constraints raise `InfeasiblePortfolio`; no silent relax
- Sample covariance is PIT; `inv` not `pinv`; non-PSD fails unless `eigenvalue_clip` is named
- Min-var long-only is projected gradient on the simplex, documented as not a commercial QP
- Mean-var `μ` is the alpha score, not future return
- ERC is long-only only
- `WeightMapStrategy` sets `Signal.score = target weight` so `construct_portfolio` and the firewall still run
- `portfolio.experiment` may import `backtest.engine`; construction must not import experiment
- `research/__init__.py` and `portfolio/__init__.py` stay thin
- Synthetic results cannot be `RESEARCH_CANDIDATE`
- Desktop Portfolio Lab is a `quantlab.app` query viewer

## Consequences
- Top-N / rank-weight remain the control experiments
- Beta, sector, ADV, NIFTY benchmark, and capacity stay `NOT_TESTED`
- Turnover stays `0.5 × L1` in both the engine and portfolio diagnostics

## References
Prompt 07; ADR-005; ADR-006; ADR-019; ADR-020
