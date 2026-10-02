# ADR-047 — Restricted-Live Eligibility Authorization

## Context

Prompt 36 needs a deterministic governance assessment after certification,
readiness, reconciliation, and production-shadow evidence. Release eligibility
must remain distinct from broker execution authority.

## Decision

Add `quantlab.execution_authorization` with immutable scope, evidence, checks,
assessment, human approval, and revocation contracts. Assessments fail closed:
critical `FAIL` and `NOT_TESTED` are retained as blockers. Automated assessment
can only return `ELIGIBLE_FOR_HUMAN_REVIEW`.

Human review requires a deliberate `APPROVE <assessment_hash>` confirmation,
is bound to the exact scope hash and expiry, and can be revoked. Neither state
records nor UI actions open a broker route.

```text
RELEASE_ELIGIBLE != EXECUTION_AUTHORIZED
HUMAN_AUTHORIZED != LIVE_TRADING
LIVE_TRADING = FALSE
BROKER_WRITE_ENABLED = FALSE
```

## Consequences

- `quantlab execution-auth` evaluates eligibility and records governance only.
- AI and system actors cannot approve.
- Mutating the scope invalidates an approval.
