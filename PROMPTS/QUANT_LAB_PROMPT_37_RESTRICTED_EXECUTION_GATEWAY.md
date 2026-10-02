# QUANT LAB — Prompt 37
## Restricted Execution Gateway — Broker Write Isolation & Human-in-the-Loop Order Control
**Target:** v3.7.0 | **Scope:** isolated extension of `quantlab.broker_gateway`

### Mission
Implement a narrow, human-mediated gateway for submitting an already-approved immutable order intent. It must not generate signals, choose securities, size positions, rebalance portfolios, or decide whether a trade is desirable. The gateway validates and mediates a human-approved request only. It remains disabled by default.

### Repository-first instructions
Inspect and compose with Prompts 13, 17, 18, 23, 25–28, 32–36 and current order-intent, risk, authorization, audit, UI, and CLI contracts. Reuse existing systems; do not create a second OMS, risk engine, broker abstraction, reconciliation engine, or ledger. If Prompt 36 is absent/incomplete, implement interfaces and mock-only tests; do not bypass authorization. Check ADR numbering.

### Hard safety invariants
- `LIVE_TRADING=false` by default everywhere.
- Default adapter is `MockBrokerAdapter`; no real write adapter is enabled by this prompt.
- No autonomous placement, modification, cancellation, retry, replacement, or batch approval.
- Every write requires fresh human confirmation bound to the exact immutable request hash and current authorization scope.
- AI cannot confirm or invoke writes. Research/model/AI packages cannot import the write adapter.
- Kill switch, expired/revoked authorization, stale account/feed, unresolved reconciliation, or scope/risk violation blocks.
- No silent normalization, symbol substitution, quantity expansion, or price change. Any change invalidates confirmation.
- Ambiguous timeout becomes `SUBMISSION_UNKNOWN`; never retry automatically. Reconcile read-only first.
- Secrets never enter logs, reports, UI state, or persisted records.

### Implementation
Keep read-only operations in the existing read-only adapter. Define a narrow write protocol for only explicitly supported order operations. Reject unsupported types.

For each request: validate account and security identity; validate order fields, units, session and broker capability; validate authorization, feed/account freshness, reconciliation, configured exposure/notional/turnover limits; create immutable envelope/hash; require human confirmation; submit once; persist response/correlation IDs; reconcile resulting state.

Use a centralized lifecycle such as:
`DRAFT → VALIDATED → AWAITING_HUMAN_CONFIRMATION → CONFIRMED → SUBMITTING → ACKNOWLEDGED | REJECTED | SUBMISSION_UNKNOWN → RECONCILED`
Invalid transitions fail closed. Cancellation is a separate human-confirmed request with its own hash.

Persist before network submission. Use stable idempotency keys. One attempt per key unless verified broker reconciliation proves safe recovery. On ambiguous outcomes, query read-only broker state; ambiguous matching requires human investigation. Preserve exact approved values. Any explicit broker tick/lot normalization must be sourced, displayed, deterministic, and reconfirmed.

### Security and interaction
Use the established secret provider and least privilege. Separate read/write credentials where supported. Require TLS verification, bounded timeouts/rate limits, masked account identity, explicit environment, and a fail-safe kill switch. Write adapter must be impossible to instantiate in ordinary tests except via a dedicated mock.

Before each write, display masked account, canonical security ID, side, quantity, type, price/trigger, product, validity, estimated notional, limits, decision lineage, authorization ID/scope/expiry, freshness, and exact request hash. Require deliberate per-request human confirmation. Confirmation expires and is invalidated by any relevant state change. No `--yes` bypass.

### CLI and desktop
Follow existing conventions; possible commands: `quantlab execution preview|validate|status|submit|cancel|reconcile`. Non-interactive submit/cancel fails closed. Add a Restricted Execution Console for one request at a time; no hidden/background submission. UI calls application services only.

### Audit
Append immutable events for request, checks, confirmation, attempt, response/ambiguity, reconciliation, rejection, cancellation, revocation, and kill-switch actions. Include UTC time, correlation ID, hashes, authorization reference, and provenance. Use existing audit storage.

### Tests
Verify fresh install cannot write; missing/expired/revoked/wrong-scope authorization blocks; stale data/account and unresolved reconciliation block; kill switch blocks; invalid limits block; AI cannot invoke; request mutation invalidates confirmation; confirmation expires and is single-use; timeout never retries; duplicate command does not duplicate submission; invalid transitions fail; cancel requires separate confirmation; rejection is preserved; secrets are redacted; no production broker calls in tests; static import boundaries; no authorization bypass; all regressions pass.

### Acceptance
Update version, changelog, architecture map, CLI/UI docs, threat model, runbook, ADR index and backlog. Report exact test results, adapter status, supported/unsupported operations, static checks, and NOT_TESTED items. Do not enable live routing or claim the platform is safe for live capital.
