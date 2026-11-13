# Nayak Quant Lab — Aligned Build Specification

**Audience:** senior engineer / Codex working in this repository

**Status:** planning authority for future implementation

**Scope:** a personal, local-first quantitative research lab for the owner. It is not an institutional firm, investment-advisory service, or a claim of future profitability.

## 1. Mission and non-negotiable outcome

Evolve the existing Quant Lab into a disciplined, reproducible research and decision-support system for personal use. The intended progression is:

```text
trusted data
  -> reproducible research
  -> robust validation
  -> deterministic portfolio and risk decisions
  -> paper operations
  -> shadow observation and reconciliation
  -> separately governed future execution assessment
```

The goal is **not** to rebuild an imaginary institutional platform. The repository already contains broad architectural coverage for data, research, features, alpha, validation, portfolio, risk, paper OMS, monitoring, shadow/replay, safety, broker observation, and an AI research desk. Future work must close the proven gaps inside those boundaries.

No component may imply that a backtest, paper result, shadow observation, or AI recommendation is profitable, tradeable, or authorized for real capital.

## 2. Existing architecture to preserve

The system has an established pipeline:

```text
data -> integrity -> research -> features/factors -> alpha/model
-> validation -> portfolio target -> risk authorization
-> paper/shadow operations -> attribution/reconciliation -> feedback
```

The following distinctions are invariants:

- Data is not a feature; a feature is not an alpha; an alpha is not a model.
- A target portfolio is not an order; a simulated order is not a broker order.
- Paper, shadow, observed and live states are distinct and must remain visibly labelled.
- Broker connectivity is not trading authorization.
- AI assistance is not authority.
- Missing, unknown, stale, warning and untested states must never be silently promoted to pass.
- `available_time <= as_of` is required wherever information availability matters.
- Synthetic or mock data cannot be relabelled as production-grade market evidence.

### Existing subsystems to extend, not duplicate

| Domain | Reuse the existing boundary | Do not introduce |
|---|---|---|
| Data | data fabric, market-data adapters, real-history bridge, dataset identity/integrity controls, read-only Kite access | a parallel data lake or uncontrolled provider cache |
| Research | research jobs, strategy DSL, feature/alpha/model engines, experiment artifacts and validation gates | a second backtester or free-form code-generation runner |
| Portfolio and risk | target portfolios, capital, risk, safety and authorization controls | a competing optimizer, ledger or risk authority |
| AI | agent desk, host-installed typed tools, citations, abstentions, debate/adjudication/calibration work | an autonomous agent platform with credentials or policy power |
| Operations | paper OMS, TCA, monitoring, shadow, replay, digital twin and reconciliation | a second event store or superficial “paper mode” |
| Execution | restricted-execution concepts, authorization and safety boundaries | a new live broker-write adapter during this programme |

The build-program and remediation documents in `docs/agents/`, `docs/development/`, `docs/`, and `PROMPTS/` are historical engineering evidence. Reconcile them against the current code before changing a shared contract; do not assume an old acceptance note proves present operational readiness.

## 3. Engineering rules

1. Preserve the dirty worktree. Do not discard, reformat, or overwrite unrelated user changes.
2. Make additive, narrowly scoped changes. Prefer extending an existing domain package over creating a new top-level platform.
3. Read the closest module documentation, contract, test and call sites before editing a shared interface.
4. Keep live trading and broker writes disabled. Do not access, print, copy, rotate or validate secrets unless the owner explicitly authorizes a bounded health check.
5. Use typed domain models and explicit state transitions. Fail closed on invalid, stale, ambiguous, or unavailable evidence.
6. Produce immutable/replayable artifacts for datasets, research runs, validation runs, targets, risk decisions, paper events and reconciliations.
7. Treat external data, model output and broker responses as untrusted inputs; validate them at the boundary.
8. Keep UI status semantically accurate. “Configured,” “connected,” “observed,” “paper,” “shadow,” “certified,” and “live” are different states.
9. No automatic promotion between research, paper, shadow and any future execution state.
10. Every change must include proportionate tests, explicit limits, and an evidence note describing what was and was not established.

## 4. Six aligned build phases

## Phase 1 — Data evidence and point-in-time coverage

### Objective

Make research inputs identifiable, reproducible, licenced/authorized where required, and suitable for the claims a research job makes.

### Build inside existing data boundaries

- Define a provider/source contract: entitlement or licence, exchange, instrument identifiers, timezone, timestamp semantics, adjustment policy, raw retention, checksum, source version, and availability time.
- Maintain dataset manifests that bind every research run to exact source snapshots and transformations.
- Add or validate point-in-time reference datasets for calendars/holidays, listings/delistings, corporate actions, index membership, sector/cap classification and fundamentals.
- Separate `exploratory real`, `research-ready`, and `point-in-time certified` dataset states. A frozen closing-price capture is useful exploratory evidence but is not automatically certified point-in-time history.
- Add data-quality scorecards for freshness, completeness, coverage, duplicate/conflicting rows, adjustment consistency, timestamp validity and reproducibility.
- Only add new provider adapters behind the existing source-policy and provenance contracts.

### Known gaps to close

- Official sourced NSE holidays.
- Licensed or otherwise authorized long-run NSE/BSE historical data.
- Historical universe and index-membership changes.
- Corporate-action and revision history.
- Point-in-time sector, market-cap and fundamentals.
- Liquidity/ADV-quality inputs.

### Acceptance evidence

A future engineer can resolve a dataset ID to its raw source, checksum, contract, known-at time, transforms and quality report. A research job fails safely when its data is not adequate for the requested claim.

## Phase 2 — Research and scientific validation

### Objective

Strengthen the existing research system so it can reject fragile ideas rather than optimize them into attractive charts.

### Build inside existing research and validation boundaries

- Use the existing bounded strategy DSL and engine-specific jobs. Signals must use completed information only; execution assumptions must be explicit and normally use the next eligible simulated price.
- Register each experiment family: hypothesis, universe, holding horizon, feature set, parameter budget, costs, slippage assumptions, date partitions and evaluator.
- Extend the current train/validation/holdout workflow with purged/embargoed walk-forward evaluation where overlap requires it.
- Add family-level overfitting evidence: PBO/CSCV when applicable, deflated-Sharpe-style diagnostics, parameter stability, subperiod/regime sensitivity, turnover/cost stress and capacity sensitivity.
- Preserve untouched evaluation periods. Any reused holdout must be permanently labelled and excluded from independent confirmation claims.
- Create an independent reproduction path that rebuilds a selection decision from immutable inputs and never silently uses the winner’s holdout to tune it.

### AI role

AI may propose structured hypotheses within approved research templates. The host validates schemas, allowed data, DSL constraints, budget and evidence references. AI may not run arbitrary generated code, alter evaluation policy, certify a result or bypass a failed gate.

### Acceptance evidence

A candidate is replayable from data, configuration, code version, costs, splits and assumptions; it remains interpretable under adverse assumptions; and selection is distinguishable from final untouched evaluation.

## Phase 3 — Portfolio construction and deterministic risk

### Objective

Produce transparent target portfolios and traceable risk decisions without confusing them with trade instructions.

### Build inside existing portfolio, capital, risk and safety boundaries

- Bind portfolio construction to validated, point-in-time exposures and factor inputs.
- Add deterministic controls for daily loss, drawdown, concentration, sector exposure, turnover, liquidity, leverage, stale pricing and allowed instruments.
- Build a real liquidity/ADV input path before treating capacity or market impact as operational facts.
- Maintain explicit covariance/estimation and scenario policies, including dated stress packs tied to a portfolio and data snapshot.
- Record every decision as accept, reduce, reject or halt, with its input evidence, limits, calculations and reason.

### Acceptance evidence

Each target has a complete lineage: research artifacts, input snapshot, optimizer/constraint outcome, risk estimate, authorization decision and state label. Invalid or missing risk evidence prevents promotion.

## Phase 4 — AI research desk integration

### Objective

Improve research throughput and review quality while keeping authority deterministic and outside the model.

### Build inside the existing agent desk and tool gateway

- Add least-privilege, read-only tools for datasets, experiment artifacts, feature diagnostics, validation outputs, paper/shadow incidents and approved knowledge sources.
- Use structured research cards for hypotheses, assumptions, evidence, proposed tests, expected failure modes and uncertainty.
- Add critic/reviewer capability that challenges unsupported claims but cannot approve models, change policy, change limits, access credentials or authorize capital.
- Measure agent reliability: schema validity, evidence-citation coverage, unsupported-claim rate, abstention quality, duplicate-hypothesis rejection and replay consistency.
- Ensure a timeout, invalid schema, unavailable evidence or ambiguous permission produces an abstention with a clear reason.

### Token and cost discipline

- Route deterministic work—validation, calculations, retrieval, filtering, data transforms and report rendering—to ordinary code, not a language model.
- Send agents small, structured evidence packets rather than whole logs, datasets or repositories.
- Cache immutable summaries by dataset/run/version; invalidate only when the bound artifact changes.
- Use a tiered model policy: inexpensive models for classification/extraction, stronger models only for bounded synthesis or adjudication, and no model call where a deterministic rule answers the question.
- Require token/cost budgets per task, per experiment family and per daily desk cycle; log requested versus actual usage.
- Cap retries and tool calls; timeouts, malformed output and budget exhaustion must abstain rather than loop.
- Prefer exact schemas, short evidence citations and bounded response fields over open-ended chat prompts.

### Acceptance evidence

AI contributions can be audited back to exact evidence and improve a defined research measure without acquiring any path to broker actions or policy changes.

## Phase 5 — Paper, shadow, reconciliation and operational evidence

### Objective

Demonstrate that the existing decision pipeline behaves coherently over time without sending broker orders.

### Build inside existing paper OMS, TCA, monitoring, shadow, replay and reconciliation boundaries

- Maintain canonical lineage: signal -> target -> risk decision -> paper order -> simulated fill -> marks -> P&L -> TCA -> reconciliation.
- Exercise sustained daily-desk and intraday replay operation over real observations with broker writes disabled.
- Add restart/recovery, stale-data, market-closure, data-conflict and kill-switch drills.
- Reconcile against a genuinely independent book or statement source only when the relevant operational stage is authorized.
- Track zero write attempts, freshness, replay equality, reconciliation breaks, unexplained P&L, recovery time and incident outcomes.

### Acceptance evidence

The system replays the same input stream deterministically, recovers from expected faults, explains state/P&L differences and maintains continuous evidence of zero broker writes.

## Phase 6 — Future constrained execution assessment

### Objective

This phase is a future certification programme, not a current implementation instruction and not permission to enable Kite order placement.

### Preconditions

- Phases 1–5 have sustained, independently reviewed evidence.
- Applicable broker, exchange, regulatory, account and family-account authorization requirements are verified for the exact intended route.
- Separate human capital-release and emergency-revocation controls exist outside AI authority.
- There is a reviewed incident, reconciliation and recovery process.

### Only then assess

- A minimal, separately certified execution gateway with narrow typed order schemas, idempotency, allow-listed instruments, hard notional/rate limits, immutable audit records and fail-closed controls.
- A restricted small-capital pilot governed by explicit human approval and independent review.

### Language decision

Keep the current Python-centered research and orchestration stack. Keep existing UI technology where it already serves the product. Consider Rust only later for a small isolated execution-control service after contracts, paper evidence and operational requirements are stable. Do not rewrite Quant Lab in OCaml or Rust as a proxy for safety.

## 5. Delivery order and engineering handoff

Implement in this order:

1. Create a single authoritative roadmap/status ledger mapping phases, existing modules, evidence, owner, dependency and release state.
2. Close authoritative data-source and point-in-time reference-data gaps.
3. Extend existing experiment/validation artifacts with family-level overfitting diagnostics and independent reproduction.
4. Add risk-limit families only after their required data is trustworthy.
5. Connect the AI desk to existing research artifacts through read-only permissioned tools and measured reliability evaluation.
6. Run and evidence daily/intraday paper-shadow operation, replay, recovery and reconciliation.
7. Keep execution behind a future no-go review until every prerequisite is demonstrated.

For each incremental task, the engineer must provide:

- a short problem statement and the exact existing module being extended;
- data/state contracts and failure behavior;
- tests at the narrowest useful layer plus relevant integration coverage;
- an immutable evidence artifact or clear documentation update;
- the known limitations and what was deliberately not claimed;
- a reviewable change set that does not alter secrets, unrelated dirty files, or live-trading configuration.

## 6. Codex execution protocol and token budget

Use the following workflow for every implementation request:

1. Read this specification, the closest package documentation, relevant tests and call sites.
2. State the existing boundary being extended and reject a duplicate architecture before coding.
3. Search narrowly first (`rg` for the domain names, contracts and tests); do not scan the whole repository unless a dependency is truly unresolved.
4. Make the smallest additive change that proves the desired contract.
5. Run focused tests first, then proportionate integration/static checks.
6. Report evidence, limitations and any remaining external dependency truthfully.

Token budget guidance:

- Start with a targeted context pack: this file, one domain document, implementation files, tests and direct call sites.
- Do not repeatedly re-read large architecture documents after extracting their relevant constraints.
- Summarize stable findings into a short task note before moving between domains.
- Parallelize independent read-only investigation only when it reduces real uncertainty; do not duplicate exploration.
- Stop and ask for a decision when a task would change account authority, broker behavior, data licensing, regulatory posture, or capital exposure.
- Never spend model tokens performing numerical work, schema validation, data filtering, or test interpretation that deterministic code can perform more reliably.

## 7. Explicit non-goals

- No claim of institutional equivalence, future profits or live-market readiness.
- No autonomous AI trading authority.
- No credentials in source, prompts, artifacts or agent context.
- No broker-write enablement as part of this plan.
- No duplicate all-purpose platform layer, data lake, backtester, OMS, risk engine, ledger or agent framework.
- No data-quality or validation label that exceeds the evidence actually available.

## 8. Definition of success

Quant Lab succeeds at each stage only when the result is more reproducible, more falsifiable, more observable, and safer to operate than before. Capability is added only after the evidence and controls needed to contain that capability are in place.
