# Backtesting protocol

1. Define the hypothesis (direction, universe, horizon).
2. Freeze a PIT snapshot (`available_time <= as_of`).
3. Set `ResearchBacktestSpec` (costs, slippage, fill=`next_bar`, seed).
4. Run the next-bar engine. Default costs are 10 bps. Zero-cost is not tradability evidence.
5. Walk-forward: train / embargo / purged labels / untouched test.
6. Robustness: cost grid (5/10/20/50/100 bps), parameter surface, regime median-splits (methodology recorded).
7. Statistics: block bootstrap + sign-flip null. Report effect size, CI, n, null model.
8. Multiple testing: count hypotheses; apply BH/Bonferroni/Holm as diagnostics; DSR/PBO only when identified.
9. Research gate. Synthetic data cannot promote as market evidence.
10. Append the ledger and write artifacts. Do not delete prior rows.

Canonical CLI:

```
quantlab slice
quantlab backtest run
quantlab validate run
quantlab research gate <experiment>
quantlab research compare <a> <b>
```
