# Market microstructure

**Status:** Prompt 13 — versioned research objects, not a live tape.

A microstructure model is a frozen assumption set:

- spread (fixed / vol-scaled / volume-scaled / historical bid-ask)
- slippage (none / fixed bps / spread fraction / vol / volume)
- impact (none / fixed / square-root / participation)
- latency (zero / fixed sessions)
- participation cap
- fill model (capped / ratio-capped / full)
- explicit `CostSchedule`

Historical bid/ask is registered (`exec_bid_ask`) and remains `NOT_TESTED` without a PIT quote dump.

Tick size rounds BUY up and SELL down so rounding cannot create price improvement.

See ADR-027.
