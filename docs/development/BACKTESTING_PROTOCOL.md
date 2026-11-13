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

The validation suite supports an explicit `cscv_blocks` opt-in for a descriptive
mean-return CSCV calculation over the configured lookback family. It aligns the
common contiguous trial history, requires equal blocks with at least two returns
each, and returns `NOT_TESTED` on missing dates, non-finite returns, tied
in-sample winners, or otherwise inadequate inputs. Its report records the block
and split counts and the individual logits; a computed diagnostic has `WARN`
status and cannot authorize promotion. It covers only that configured family:
other prior or concurrent trials may be missing. The same history is reused
across CSCV partitions, so this does not establish an untouched holdout,
point-in-time data integrity, or tradability. A single pair of aggregate
in-sample/out-of-sample vectors is not CSCV and does not produce a PBO.
Method reference: Bailey et al., [The Probability of Backtest Overfitting](https://escholarship.org/uc/item/4w1110bb).

Canonical CLI:

```
quantlab slice
quantlab backtest run
quantlab validate run
quantlab research gate <experiment>
quantlab research compare <a> <b>
```
