# Phase 47 — Position Intelligence Loop

## Delivered local contracts

- Frozen `PositionReviewContext` includes paper/shadow mode, original candidate,
  level and exit-policy lineage, thesis, fill evidence, market snapshot, P&L
  attribution, factor/regime/volatility/liquidity/risk state, review trigger, and
  exit-rule state.
- Independent Bull and Bear views must reference the exact same frozen context.
- The deterministic reducer makes triggered exit rules authoritative; commentary
  cannot override a hard exit. Stale market state and externally closed positions
  stop ordinary assessment.
- Immutable assessment and persisted review-schedule contracts survive restart.
- The native Position Intelligence view displays history and records only research
  proposal requests. A requested add/reduce/exit must enter the full candidate flow;
  it cannot change a position or submit an order.

No continuous LLM polling loop or live broker integration is introduced. Acceptance
is pending the consolidated 45–48 release gate.
