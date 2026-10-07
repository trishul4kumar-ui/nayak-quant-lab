# Phase 46 — Trade Decision Console

The native console presents a frozen candidate, deterministic levels/exit policy,
research summaries, blockers, and provenance hashes. It supports audit-only review
intent: reject, watch, request refresh, request validation, and paper approval where
the candidate remains fresh and ready.

`APPROVE & STAGE` and `PLACE ORDER` are rendered disabled. No broker client, size,
price, account, staging, or order submission argument is exposed by this module.
Every console open/action is recorded in the existing audit ledger with
`NO_EXECUTION_AUTHORITY`.

Acceptance remains pending the one consolidated 45–48 release gate.
