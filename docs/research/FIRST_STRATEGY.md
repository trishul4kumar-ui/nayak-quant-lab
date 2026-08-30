# Research

First strategy: cross-sectional momentum (`quantlab.research.momentum`).

Purpose: validate the pipeline (MarketState → genome → risk → next-bar backtest), **not** maximize Sharpe.

`momentum_20` is 20 **trading sessions** on the research calendar, not 20 calendar days. The Prompt 06 feature engine uses the same formula. `quantlab research feature momentum_20` runs IC/quantiles/decay; that is not a promotion path.

The synthetic universe plants distinct drifts so ranking is non-degenerate. Reported Sharpe on this slice is an architecture diagnostic, not a claim of tradable alpha. The slice reads bars from the PIT fabric (`data_kind=synthetic`).

Research-grade validation (`quantlab validate run`) wraps the same engine: walk-forward, cost/parameter surfaces, bootstrap, and a gate that **cannot** promote synthetic results to paper. See [BACKTESTING_PROTOCOL.md](../development/BACKTESTING_PROTOCOL.md).
