# Bounded debate protocol — 42-v1

A debate freezes one Bull and one independent Bear initial memo on the same
canonical snapshot, PIT history, universe/scope, source versions, data kind and
mode. Different creation timestamps do not make identical historical frames
different evidence; changed bars/snapshot/scope do. Both initial research records
and their exact tool references must resolve. The earlier initial-context TTL wins.

One critique each follows, with at most three approved tool requests per analyst.
New tool results enter the shared evidence set before the next turn, and remain in
the transcript even when unavailable. An optional explicit checkbox/`--rebuttals`
allows one rebuttal each after both critiques. Rebuttals cannot request tools.
Then the protocol stops. No recursion, hidden peer evidence, opponent edits or
judge model. Critic severity/confidence and arguments are unverified opinions.

Default cost budget is two critique calls, 2,800 output tokens each, at most one
schema retry per call, a 30-second deadline including that retry, and 48,000
compact evidence characters per request. Optional rebuttals add two calls capped
at 1,600 output tokens each. Worst requested output caps are 11,200 tokens without
rebuttals / 17,600 with rebuttals and all schema retries; these are not billed-usage
measurements. There are no extra hidden planning calls. Run claims are permanent:
crashes cannot automatically replay paid work. A finished session returns its
hash-verified stored transcript; an interrupted claim requires fresh initials.

Provider failure/timeout, invalid output, cancellation or missing opposing provider
produces INCOMPLETE without fabricating a view. Expiry produces STALE and discards
late output. Persistence failure blocks; there is no memory fallback. A new frozen
source or a new pair of initials yields a different debate identity.

## Falsification boundary

Named routes expose OOS/walk-forward, robustness, multiple testing, factor
explanation, regime dependence, cost resilience, liquidity, parameter fragility,
benchmark alternatives and test-set integrity through the canonical typed gateway.
Only an exact named canonical result counts for a check. Descriptive beta/regime,
model prose and unrelated PASS metrics do not prove independent edge. Incomplete
typed adapters/inputs remain UNAVAILABLE/NOT_TESTED. No quantitative engine is
reimplemented here, and no argument can promote those gaps to PASS.

## UI and CLI

Run both initials using the same saved inputs, then open **Debate Arena** and choose
**Debate latest frozen memos**. Rebuttals are off by default to keep usage bounded.
The native transcript/check panels are resizable and always available; saved
transcripts can be selected. The optional local Three.js graph shows role nodes,
shared evidence, interpretation edges and real active states. Evidence and the
center transcript button navigate only to published, hash-verified native records.
The neutral center explicitly says adjudication is not built yet.

```sh
python -m quantlab.cli agents run-debate --bull-memo BULL_HASH --bear-memo BEAR_HASH
python -m quantlab.cli agents debate-history --query SNAPSHOT_HASH
```

The transcript contains protocol/session hashes, both initials, critique/rebuttal
hashes, source evidence graph, named checks, aware start/completion clocks and
failure codes. Readers verify context ancestry, all references, targets, tool
requests, shared source boundaries, derived checks, turn counts and clocks. Hashes
are deterministic from the stored artifacts; the model conversation itself is not.
COMPLETE means the finite research protocol finished, not that tests passed or a
trade is authorized. Execution authority remains false.
