# Phase 41 — Independent Bear analyst

Implemented only after Phase 40's published CI acceptance. Phase 41 release gates
are in progress; this report does not imply completion of Phases 42–53 or live
trading readiness.

Bear owns a downside mandate, strict draft/memo contract, independent model calls,
evidence interpretation and searchable history. Its initial prompt never receives
Bull's memo, score or references. Both analysts can bind to identical immutable
snapshots/history without sharing interpretations. The common bounded lifecycle
was extracted without changing existing Bull artifact names or payload fields.
An existing Phase 40 memo was successfully hash-verified after the refactor.

Every Bear memo includes support/contradictions, mandatory evidence sections, all
seven self-falsification answers, explicit invalidations, squeeze/reversal and
liquidity risks, exposure intent, raw confidence and uncertainty. Instrument
eligibility remains UNKNOWN and positions NOT_TESTED. Missing validation/TCA cannot
yield a trade-ready short conclusion. NO_TRADE and AVOID are valid results.
Existing factor/regime adapters remain descriptive; the other incomplete typed
adapters remain honestly UNAVAILABLE/NOT_TESTED, not model-generated PASS results.

The native Bear workspace mirrors Bull's resizable evidence, memo, challenge,
actual tool/state timeline and searchable history, with distinct downside/risk
language. Both run buttons have blocking feedback, run in cancellable background
jobs, and serialize desk runs. Evidence navigation selects the correct analyst's
native result. Bear panel preferences persist independently without an outer
nested terminal splitter. Model text is displayed as plain text.

## Verification evidence

- Tests cover independence on the same frozen source, permission symmetry, AVOID,
  self-invalidating NO_TRADE, UNKNOWN eligibility, missing/unhealthy market input,
  missing historical support, stale-before-freeze, live-tool/sizing/price rejection,
  foreign references, mandatory falsification/risk fields, searchable history and
  restart without another model call.
- Native button/history/evidence navigation and panel persistence are tested;
  both analyst inspectors are exercised at 1024×640, 1280×800, 1512×982 and 1920×1080.
- Agent and flowing-layout regressions: **89 passed**. Optimized-mode safety suite:
  **223 passed** (the expected Python `-O` assertion warning). Ruff and strict mypy
  passed across 831 source files.
- No real model/broker request, safety-flag change or live order was used in tests.
- Final full-suite, optimized-mode, distribution and published CI results will be
  recorded after completion. Code and fixture tests do not establish profitable
  research, calibrated performance or real-market production readiness.
