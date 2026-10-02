# ADR-048 — Restricted Execution Gateway

## Context

Prompt 37 requires a narrow broker-submission boundary without broadening the
research platform into an autonomous execution system.

## Decision

Add `quantlab.restricted_execution` with immutable order envelopes, exact
human-confirmation text, scope-bound approval checks, one-attempt submission,
and explicit `SUBMISSION_UNKNOWN` handling. The packaged adapter is disabled;
the only submit-capable adapter is a network-free test double.

```text
RESEARCH / AI -> cannot import or invoke production broker writes
UNCONFIRMED / EXPIRED / KILLED -> BLOCK
TIMEOUT -> SUBMISSION_UNKNOWN -> READ-ONLY RECONCILIATION
```

## Consequences

- The CLI can preview, validate, and inspect state, but submit/cancel fail
  closed because a terminal is not a human confirmation ceremony.
- Neither request data nor gateway logic creates signals, sizing, routes, or
  replacements.
- A real broker write adapter is intentionally not included or enabled.
