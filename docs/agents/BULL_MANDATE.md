# Bull mandate and operating boundary

Bull investigates long-side momentum, continuation, relative strength, breakouts,
pullbacks, breadth, factor exposure, regime, volatility, liquidity, model/ensemble
support and approved catalysts. It must seek contradictions, invalidation, beta or
factor explanations, costs, OOS/walk-forward survival, regime dependence and missing
data. All seven challenges are required in its structured memo.

Screening produces a reproducible research queue, never a buy instruction. Raw
confidence is an opinion. Quantity, numerical execution levels, calibration,
permissions, broker writes, risk overrides and release authorization are forbidden.
Missing canonical validation or TCA automatically downgrades `LONG_CANDIDATE` to
`MORE_RESEARCH`. `NO_TRADE` is a successful result, not a failed job.

Run from Full Lab → Research → AI Quant Desk. Load a frozen snapshot, optionally
load PIT history, and click **Run Bull research**. The latest already-captured app
snapshot may also be used. Nothing automatically polls a source or substitutes mock
data. Historical input requires the explicit **Replay** checkbox. Unhealthy inputs
remain blocked even in replay. Cancel is connected to the background job and model
deadline; late responses cannot freeze a memo.

Model configuration is local `.env` or environment: `OPENAI_API_KEY` and an explicit
`QUANT_LAB_AGENT_MODEL`. Do not put credentials into research text or chat.
Configuration is not verified connectivity. No default paid model is selected.

CLI:

```sh
python -m quantlab.cli agents run-bull --snapshot /absolute/path/snapshot.json --replay
python -m quantlab.cli agents bull-history --query momentum
```

Optional history JSON has exactly `bars`, `price_basis`, and `data_kind` keys. Bars
use the existing `OHLCVBar` contract with instrument identity and all PIT clocks.
The context checks scope, availability, data kind and price basis against the frozen
snapshot. Imported markers are lineage labels, not external proof of real data.

Budget: at most 20 names, 5,040 history bars, 12 tool attempts, three optional
analyses, five prior Bull theses knowable at the input boundary, and 24,000 evidence
characters per model request. Two schema-bounded requests use 1,000/2,400 maximum
output tokens; one schema retry per request caps requested output at 6,800 tokens.
Each request has a 30-second total deadline including its retry. This is a configured
ceiling, not a measurement of provider-billed usage. State/history reads do not call
the model. Completed run replay uses its persisted record without another model call.

An atomic durable claim prevents duplicate execution of a run across processes.
Interrupted claims are not automatically retried: create a new frozen run. Existing
artifacts remain immutable. History supports scope/thesis/contradiction/invalidation
search; realized outcomes, false-breakout classifications and calibrated confidence
remain `NOT_TESTED` until source-backed outcome records exist in later phases.
