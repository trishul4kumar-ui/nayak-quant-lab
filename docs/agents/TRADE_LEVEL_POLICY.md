# Trade-level policy — Phase 44

`44-v1` produces deterministic, research-only price-level plans. It is not a
strategy, sizing rule, order instruction, execution authority or profitability
claim.

## Inputs and boundary

`TradeLevelInput` is a sealed, hash-addressed artifact. It requires a verified
dominant adjudication identity, matching snapshot identity, security identity,
price/quote state, approved ATR, regime, session, tick size and a named
corporate-action adjustment policy. Adjusted history and raw quotes may not be
mixed. Missing, invalid, stale or one-sided quote inputs are rejected; nothing
is guessed.

The service verifies that the stored adjudication is not `NO_TRADE`, that its
outcome matches the requested direction (`BULL_DOMINANT` → `LONG`,
`BEAR_DOMINANT` → `SHORT`), and that the snapshot identity matches before
calculation. It contains no broker, provider, portfolio, quantity or order
dependencies.

## Arithmetic

The versioned policy uses a 0.10 ATR entry band, 1.00 ATR protective stop,
1.25 ATR hard invalidation, 2.00/3.00 ATR targets, 1.50 ATR trailing rule and
instrument tick rounding. The appropriate direction is enforced mechanically:

- A long plan has invalidation < stop < entry < targets.
- A short plan has targets < entry < stop < invalidation.

`NO_VALID_ENTRY` is a successful abstention with no numerical entry, stop,
target or exit policy. Plans contain no quantity field.

## Freshness and presentation

Plans expire at their supplied boundary. `evaluate_plan_freshness` produces a
separate immutable assessment when expiry, a price move above 75 bps, a 1.5x
ATR change or a regime change occurs. It never mutates or chases a frozen plan.

`TradeChartOverlayDTO` is presentation-only: entry band, invalidation, stop,
targets, trailing rule and evidence identities. The desktop Levels inspector is
read-only and has no order controls.

## CLI

```text
quantlab trade-levels compute --input frozen-level-input.json
quantlab trade-levels inspect PLAN_HASH
quantlab trade-levels history
```

The CLI accepts no quantity, order type, broker credential or live-trading
argument. A blocked input and a `NO_VALID_ENTRY` response use a non-zero exit
code.
