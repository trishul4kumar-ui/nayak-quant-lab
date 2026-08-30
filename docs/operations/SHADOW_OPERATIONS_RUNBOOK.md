# Shadow Operations Runbook

**Version:** 2.4.0

```bash
quantlab shadow health
quantlab shadow status
quantlab shadow run --mode research_paper
quantlab shadow run --mode paper
quantlab shadow run --mode shadow
quantlab shadow reconcile
quantlab shadow replay last
quantlab shadow audit
```

Keep `LIVE_TRADING=false`. Do not set `BROKER_PASSWORD`, `LIVE_ACCOUNT_ID`, or `LIVE_ORDER_TOKEN` on this path.

If the engine is `PAUSED`, no new decisions are generated. If `HALTED`, new exposure is rejected. HALT is not auto-liquidation.
