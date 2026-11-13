# Local AI research desk — phases 1–6 implementation boundary

This is an implementation map, not evidence that a trading system is ready to trade or make money.
`LIVE_TRADING=false` and `BROKER_WRITE_ENABLED=false` remain required. The local model is a
research component; it has no broker credential, order, release, limit, or permission authority.

## Phase 1 — AI research desk

`quantlab.agent_desk.supervisor.route_research_job` is the deterministic supervisor gate. It maps
bounded desk jobs to the supervisor, bull, bear, document/news, quant, risk, execution-monitor,
or audit/compliance role. Each assignment is a hash-sealed artifact with
`execution_authority=false`. The gate does not call an LLM or any tool itself.

Every assigned job needs a frozen snapshot hash plus one or more matching frozen evidence references
whose status is `PASS` or `WARN` and whose availability time is no later than the assignment time.
Missing, unknown, failed, stale/mismatched, or future evidence yields an `ABSTAIN` artifact. Document
content is evidence data only and cannot change routing, scope, authority, or the fixed claim rule.

Existing bull/bear workers, the typed provider runner, canonical read-only tools, debate, and
adjudication remain the only research path. The local Ollama adapter receives a fixed system policy
and strict JSON schema; it cannot obtain an execution adapter through this desk.

## Phase 2 — Deterministic portfolio desk

Existing `portfolio`, `risk`, `trade_candidates`, `realtime_decision`, `release`, and `safety`
packages retain strategy selection, portfolio construction, risk firewalls, release evidence, and
abstention behavior. Supervisor assignments can request research only; they cannot mutate strategy
code, risk limits, release state, or AI permissions.

## Phase 3 — Paper and digital twin

Existing `paper_oms`, `digital_twin`, and `shadow` packages own simulated intents, orders, fills,
slippage, shadow state, reconciliation, and recovery. Agent-desk artifacts are intentionally
non-routable inputs and cannot place, modify, or cancel an order.

## Phase 4 — Production shadow

Existing `production_shadow` and read-only broker gateway evidence retain observed-account comparison
and reconciliation. Acceptance still requires a sustained evidence window, stable data quality,
reconciliation, and compliance review; none of that evidence exists merely because the code is present.

## Phase 5 — Restricted automation

Existing `restricted_execution`, `execution_authorization`, release, safety, and kill-switch controls
remain separate from this desk. This phase is not activated. It requires independent human and legal/
broker approval plus bounded capital, expiry, reconciliation, signed release, and a working kill
switch. No AI role can issue an order or clear/certify those controls.

## Phase 6 — Ongoing operations

Existing `monitoring`, `live_ops`, reconciliation, drift, incident, and rollback controls remain the
operational source of truth. The desk can prepare evidence and anomalies only. Any unknown or anomalous
state must abstain or halt through deterministic host controls; it cannot self-approve a resume.

## Acceptance status

Phase 0 local-foundation software and Phase 1 supervisor routing have local implementation and tests.
Phases 2–6 have existing control-plane software mapped above, but their operational acceptance gates
remain unproven until real, independently reviewed paper/shadow evidence is collected. No live
automation was enabled by this work.
