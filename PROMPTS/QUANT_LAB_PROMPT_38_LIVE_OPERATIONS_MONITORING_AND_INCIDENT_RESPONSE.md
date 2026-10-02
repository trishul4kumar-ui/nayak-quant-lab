# QUANT LAB — Prompt 38
## Live Operations Monitoring, Exposure Surveillance & Incident Response
**Target:** v3.8.0 | **Package:** `quantlab.live_ops` or a compatible extension of `quantlab.ops`

### Mission
Build continuous, auditable surveillance across data → decision → authorization → gateway → broker observations → fills → positions/cash → reconciliation → portfolio/risk → system health. This is monitoring and incident response, not alpha generation, portfolio alteration, order routing, or autonomous repair.

### Repository-first instructions
Inspect and reuse Prompts 13, 18–21, 25–31, 32–37 and existing event, health, audit, notification, persistence, CLI, UI, and runbook conventions. Extend existing services; do not create parallel monitoring, risk, OMS, kill-switch, or ledger systems. Check ADR index for the next unused number.

### Safety principles
- A green dashboard never grants authorization.
- Alerts and incident automation never create, modify, or cancel broker orders.
- Automated responses are limited to explicitly pre-authorized fail-safe actions already supported by safety/ops, such as pausing new submissions or engaging the existing kill switch.
- No automatic resume after a critical halt; human review and existing authorization flow are required.
- AI cannot close incidents, waive controls, or resume execution.
- Missing/stale/inconsistent evidence fails closed; preserve chronology and raw evidence.
- Do not log secrets or unnecessary personal/account data.

### Monitoring domains
1. **System/deployment:** liveness, version/config hash, clock drift, CPU/memory/disk, DB health, backup age/restore-test status, audit integrity, worker heartbeat/queue lag, crashes/restarts.
2. **Market data:** connectivity, sequence gaps/duplicates/out-of-order events, event/receive latency, staleness, session/calendar mismatch, security-master failures, corporate-action/reference-data freshness, failover and provenance.
3. **Decision pipeline:** state freshness, feature/alpha/model/ensemble lineage hashes, latency/missed cycles, abstention/gate reasons, risk outcomes, target hash, replay comparison. Do not recompute or silently substitute signals.
4. **Broker/execution:** authorization scope/expiry/revocation, gateway status, pending/unknown submissions, acknowledgement/rejection latency, lifecycle aging, API errors/rate limits, account snapshot freshness, fill/position/cash discrepancies, unresolved reconciliation.
5. **Portfolio/risk:** cash/reserved cash, gross/net exposure, concentration and configured-limit utilization, P&L with methodology/source, drawdown/loss-limit utilization, turnover/cost drift, supported factor/regime exposure. Unavailable metrics are NOT_TESTED, never zero. Distinguish broker-reported, internally calculated, estimated, and unavailable values.

### Contracts and incident lifecycle
Add typed/versioned contracts: `HealthSignal`, `AlertRule`, `AlertEvent`, `Incident`, `IncidentEvent`, `IncidentEvidence`, `ResponseAction`, `OperationalSnapshot`, `EscalationPolicy`.

Use deterministic configurable severities `INFO`, `WARNING`, `HIGH`, `CRITICAL`. Lifecycle:
`DETECTED → ACKNOWLEDGED → INVESTIGATING → MITIGATED → RESOLVED → CLOSED`, with `REOPENED` when new evidence appears. Preserve every transition and actor. Human closure requires rationale and evidence; critical incidents cannot close while their blocking condition persists.

Deduplicate by stable fingerprint while retaining occurrence count/timestamps. Rate-limit notifications without discarding evidence.

### Fail-safe response
Support only configured, monotonic-to-safer actions already implemented in safety/ops: notify, pause new submissions, engage existing kill switch, halt affected subsystem, request investigation. Record trigger evidence and policy version, execute idempotently, verify resulting state, emit incident event, and require human review before resumption. No auto-restart-to-trading.

### Persistence and notifications
Use existing audit/event storage. Persist immutable signals, rules, incident timeline, action results, operator decisions, correlation IDs and hashes. UTC and deterministic serialization required. Provider-neutral notifications: local/in-app first; external channels optional and disabled by default. Delivery failure cannot erase incidents or change safety state. Redact secrets.

### CLI and desktop
Follow existing patterns; possible commands: `quantlab live-ops status|health|alerts|incidents|incident show|incident acknowledge|incident resolve|audit`. Add Live Operations Center with distinct system/data/decision/broker/reconciliation/portfolio/risk panels; PASS/WARN/FAIL/NOT_TESTED; incident timeline; authorization and kill-switch state; unknown submissions; freshness/provenance. Keep operational health separate from release certification and execution authorization.

### Tests
Test stale feeds, sequence gaps, clock drift, stale account snapshots, unknown submissions, unresolved reconciliation, idempotent kill-switch action, no order writes from responses, no auto-resume, notification failure, deduplication with occurrence retention, critical incident closure prevention, human rationale, audit corruption, secret redaction, missing metrics as NOT_TESTED, deterministic rules, no duplicate ledger/risk engine, and full regression suite. Use mock providers only.

### Documentation and acceptance
Update version/changelog, architecture map, CLI/UI docs, alert reference, incident/recovery runbooks, ADR index and NOT_TESTED backlog. Report changed files, event flow, safety boundaries, exact test counts, static checks, limitations, and operator procedures. Monitoring coverage is not production readiness and does not grant permission to trade.
