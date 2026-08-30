# ADR-019 — Research-grade validation around the existing backtester

## Context
Prompt 05 requires walk-forward, robustness, statistical tests, multiple-testing diagnostics, and a research gate. The Day-1 engine already fills next-bar with 10 bps default costs.

## Problem
A second backtester would fork fill/cost semantics and let a “research” path silently disagree with production research.

## Options
1. Rewrite `run_backtest` as a vectorized research engine
2. Wrap the existing engine with a validation suite and typed config identity
3. Add SciPy/statmodels and treat p < 0.05 as promotion

## Decision
Option 2.

- `BacktestConfig` remains the execution contract (`fill_policy=next_bar` only)
- `ResearchBacktestSpec` + `config_hash` identify a research configuration
- `quantlab.research.suite` runs walk-forward, cost/parameter grids, block bootstrap, FDR/FWER, and the gate
- Annualization is centralized (`quantlab.math.annualization`); risk-free rate is explicitly 0, not an Indian T-bill
- Indian tax/fee legs default to 0 with provenance “unspecified, not invented”
- Synthetic `data_kind` cannot become `RESEARCH_CANDIDATE` or `PROMOTED_TO_PAPER`
- Full CSCV PBO is not manufactured; under-identified diagnostics stay `NOT_TESTED`
- Desktop Validation is a client of `quantlab.app`; it does not run on every Backtest click
- No live-trading promotion state

## Consequences
- Slice metrics stay comparable to Prompts 02–04
- A failed gate is a successful research outcome
- Official NSE holidays, licensed dumps, factor libraries, and calibrated impact remain `NOT_TESTED`

## References
Prompt 05; ADR-005; ADR-011; ADR-013; ADR-015
