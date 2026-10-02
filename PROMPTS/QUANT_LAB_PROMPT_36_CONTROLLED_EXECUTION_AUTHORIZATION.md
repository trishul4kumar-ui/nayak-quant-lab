# QUANT LAB — Prompt 36
## Controlled Execution Authorization & Restricted-Live Eligibility Engine
**Target:** v3.6.0 | **Package:** `quantlab.execution_authorization`

### Mission
Build a deterministic, fail-closed authorization assessment that evaluates whether a specific deployment, account, universe, model/strategy lineage, risk policy, and time window may be presented for restricted-live human approval. This is an eligibility and governance layer only. It must not place, modify, or cancel broker orders.

### Repository-first instructions
Inspect the repository, current architecture, CLI/UI conventions, tests, ADR index, and implementations of Prompts 23, 25–35. Reuse existing release certification, safety, ops, broker read-only, reconciliation, market-data, production-shadow, digital-twin, and audit contracts. Do not create duplicate engines or ledgers. Check actual ADR numbers; use the next unused number. If a prerequisite is absent, mark it NOT_TESTED and block; do not build a bypass.

### Non-negotiable invariants
- `LIVE_TRADING=false` remains the default in fresh installs, tests, CI, and examples.
- `RELEASE_ELIGIBLE` is not `EXECUTION_AUTHORIZED`.
- Automated evaluation may return `ELIGIBLE_FOR_HUMAN_REVIEW`; it may never create human authorization.
- AI/LLM output is suggestion-only and cannot approve, sign, waive, unlock, or authorize.
- Kill switch, identity mismatch, stale data, unresolved reconciliation, missing audit evidence, and risk-limit violations are non-waivable.
- Missing, stale, contradictory, malformed, or unverifiable evidence fails closed.
- Preserve PASS/FAIL/NOT_TESTED distinctly. Critical NOT_TESTED blocks.
- No silent defaults, repairs, promotion, or implicit consent. Never expose secrets.

### Scope and contracts
Create typed, versioned, immutable contracts following existing conventions:
- `AuthorizationScope`: deployment, broker/account fingerprint, allowed canonical security IDs and universe version, strategy/model/portfolio hashes, release reference, data provider/policy, risk policy, explicit exposure/notional/turnover limits, operating mode, session window, expiry.
- `AuthorizationEvidence`: source, provenance, timestamp/freshness, content hash, linked report ID.
- `AuthorizationCheck`: stable check ID, result, severity, evidence, reason.
- `AuthorizationAssessment`: exact scope, checks, blockers, evidence hashes, deterministic assessment hash.
- `HumanApprovalRecord`, `AuthorizationRevocation`, `AuthorizationPolicy`.

Use existing storage/audit abstractions; do not create a second general ledger. Canonical serialization, UTC timestamps, schema versions, stable IDs, and SHA-256 hashes are required. Never invent numeric risk limits: absent or invalid limits mean ineligible.

### Required assessment gates
Check: current release and Prompt 23 certification; Prompt 25 safety state; Prompt 26 operational health and recovery posture; account identity; freshness/provenance of broker observation; latest reconciliation; production feed health, clock, sequence, session and staleness; Prompt 35 shadow duration/session policy and critical incidents; deterministic replay evidence where policy requires; explicit internally consistent risk limits; complete hash-verifiable audit evidence. Missing evidence is NOT_TESTED.

### State machine
Support `BLOCKED`, `INELIGIBLE`, `ELIGIBLE_FOR_HUMAN_REVIEW`, `HUMAN_AUTHORIZED`, `EXPIRED`, `REVOKED`. Evaluation cannot set HUMAN_AUTHORIZED. Human approval must be explicit, bound to exact package hash and scope, expiring, attributable, and revocable. Any change invalidates approval. Require a deliberate confirmation, show all checks/limits/blockers/expiry, and record approval evidence. No blanket approve-all.

### CLI and desktop
Follow existing conventions; add `quantlab execution-auth assess|package|status|approve|revoke|audit`. Assessment/package are read-only. Approve/revoke require interactive human action and durable audit. Add an Execution Authorization Lab as a client of application services, showing scope, evidence freshness, PASS/FAIL/NOT_TESTED, blockers, package hash, expiry, and immutable history. UI must not implement policy or write storage directly.

### Tests
Test default unauthorized state; release eligibility not sufficient; AI cannot approve; missing/critical NOT_TESTED blocks; stale feed/account, identity mismatch, unresolved reconciliation, kill switch, invalid limits, unverifiable evidence all block; no waiver of safety controls; exact-hash approval; mutation invalidates approval; expiry/revocation; concurrent/duplicate actions; deterministic evaluation; secret redaction; no broker writes/imports; `LIVE_TRADING=false`; full regression suite. Synthetic fixtures are diagnostic only, never production evidence.

### Documentation and acceptance
Update version/changelog, architecture map, README/CLI help, safety/threat docs, ADR index, backlog and NOT_TESTED register. Report changed files, commands, exact test counts, static checks, limitations, and unresolved items. Do not claim production readiness or enable live trading.
