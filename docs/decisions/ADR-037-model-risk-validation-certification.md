# ADR-037 — Model Risk, Independent Validation & Pre-Live Certification

## Context
Prompt 23 asks whether a research strategy/model is evidenced, reproducible, robust, and independently validated enough to progress to the next **controlled** stage. Certification is governance, not broker permission.

## Decision
Add `quantlab.certification` wrapping Prompts 04–22. The state machine is strict (`DRAFT → … → CERTIFIED`) and never allows `DRAFT → CERTIFIED` or research → live. FAIL, critical `NOT_TESTED`, unresolved reconciliation, synthetic production evidence, and safety failure block `CERTIFIED`. AI cannot override certification. Top-level CLI is `quantlab validation` (not Prompt 05 `quantlab validate`). Desktop nav key is `certify` (**Validation & Certification Lab**).

## Consequences
- Missing evidence is `NOT_TESTED`, never a silent PASS
- `CERTIFIED` is not live order authority
- Material/major changes require a new candidate version and revalidation
- `LIVE_TRADING` remains false; no broker imports
