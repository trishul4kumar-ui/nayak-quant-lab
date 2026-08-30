# Research gates

Outcomes:

```
REJECT | WARN | RESEARCH_CANDIDATE | PROMOTED_TO_PAPER
```

There is no live-trading outcome.

Hard rejects include integrity FAIL, same-bar fill, zero costs, and using the test set for selection.

`data_kind=synthetic` cannot be `RESEARCH_CANDIDATE` or `PROMOTED_TO_PAPER` (maximum `WARN`).

AI cannot grant `OVERRIDE_RESEARCH_GATE` or `REQUEST_LIVE_ORDER`.

A failed gate is a valid research result. It is recorded, not rewritten.
