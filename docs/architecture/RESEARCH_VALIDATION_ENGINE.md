# Research validation engine

The validation layer wraps the existing next-bar backtester. It does not replace it.

See [ADR-019](../decisions/ADR-019-research-validation.md).

```
PIT snapshot
  → typed ResearchBacktestSpec (hashed)
  → next-bar backtest (10 bps default)
  → performance + drawdown episodes
  → walk-forward (rolling / expanding / anchored)
  → cost / parameter / regime robustness
  → block bootstrap + sign-flip null
  → BH / Bonferroni / Holm + deflated Sharpe
  → research gate
  → append-only ledger + artifacts
```

UI Backtest Lab still runs the **slice**. Full validation is `quantlab validate run` or the desktop Validation page.

Synthetic results are architecture evidence only.
