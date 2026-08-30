# ADR-033 — Portfolio Monitoring, Attribution & Research Feedback

## Context
Prompt 19 asks QUANT LAB to explain what happened after an investment decision: P&L, attribution, drift, risk, and research feedback — without becoming a second backtester or changing the decision.

## Decision
Add `quantlab.monitoring` as a post-decision observation layer. It consumes Prompt 18 paper books and Prompt 17 targets. Prompt 05 remains the only promotion gate. Unknown P&L legs stay `None` / `NOT_TESTED`. Residuals stay visible. NIFTY is not fabricated.

## Consequences
- `PERFORMANCE ≠ ATTRIBUTION ≠ ALPHA ≠ CLAIM`
- Desktop Monitoring Lab is a query view of `quantlab.app.monitoring`
- `LIVE_TRADING` remains false
