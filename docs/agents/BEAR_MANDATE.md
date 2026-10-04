# Bear mandate and operating boundary

Bear researches downside economics independently of Bull: negative momentum,
breakdowns/failed breakouts, mean reversion against longs, volatility expansion,
tail/drawdown conditions, crowding/correlation, liquidity, adverse regimes and
squeeze/reversal risk. It must seek evidence against its own thesis and can
successfully conclude AVOID, REDUCE, HEDGE, EXIT, MORE_RESEARCH or NO_TRADE.

Exposure archetypes are research intent only: AVOID, SELL_EXISTING,
INTRADAY_SHORT_RESEARCH, FUTURE_SHORT_RESEARCH, PUT_RESEARCH, HEDGE_RESEARCH and
NO_VALID_EXPOSURE. Instrument eligibility is host-owned UNKNOWN in this phase.
No overnight cash-equity short or existing position is assumed. Bear cannot size,
set broker prices, submit orders, override risk or change its own permissions.

Initial research accepts only a frozen snapshot, optional matching point-in-time
history, its own knowable prior hypotheses, and canonical tool results. It cannot
read Bull's initial memo; cross-agent critique is a separate Phase 42 operation.
Both initial memos must share the same frozen evidence boundary for a debate.

## Bounded usage

Identical infrastructure limits to Bull: 20 securities, 5,040 history bars, five
knowable own prior theses, nine compulsory tool attempts and at most three optional
analyses, two structured calls, 24,000 evidence characters, 30 seconds per call and
one schema retry. Requested output caps are 1,000/2,400 tokens (6,800 with both
retries); these are caps, not measured billed usage. Shared transport prevents
overlapping timed-out requests to the same provider instance. Run claims persist
across restarts; interrupted paid work cannot automatically replay.

Use the native **Run Bear research** control, or:

```sh
python -m quantlab.cli agents run-bear --snapshot /absolute/path/snapshot.json --history /absolute/path/history.json
python -m quantlab.cli agents bear-history --query liquidity
```

Add `--replay` only for explicit historical/synthetic research. Configuration and
input format are documented in BULL_MANDATE.md. Missing credentials/data produce
visible blocking feedback, not an automatic mock fallback. Raw confidence is an
opinion; calibrated confidence and realized outcomes remain NOT_TESTED until
Phase 48 supplies independently time-bound outcome records.
