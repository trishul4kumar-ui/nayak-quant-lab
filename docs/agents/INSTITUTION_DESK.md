# Institutional AI research desk

The desktop AI Quant Desk has an Institution view with a local Three.js team and an
interactive NAYAK console. Its Python service runs Bull, Bear, News/Documents,
Quant, Risk, Execution Monitor and Audit in sequence, then asks the Desk Supervisor
to consolidate their frozen reports. A progress callback publishes the actual role
state to the visual view. The animation is a presentation of recorded work, not a
separate execution engine.

`InstitutionDeskService(repository, provider).run(snapshot, now=..., replay=False,
history=None, documents=(), cancel=None, progress=None)` returns a frozen
`DeskCycle`. `ask(cycle_hash, question, now=..., cancel=None)` returns a frozen
`NayakAnswer`. `latest()` and `verify(cycle)` resolve persisted provenance before
presentation or questioning. `cycle.presentation()` creates independent dictionaries
for the eight role figures.

Bull and Bear use the existing analyst lifecycle and canonical typed tool gateway.
The five support roles use compact structured JSON and receive only host-selected
evidence. Snapshot-bound candidate packets, position assessments, paper eligibility
and lineage, and daily-desk state are read from the existing artifact repository.
Portfolio-wide risk, account/fill reconciliation and unbound validation/backtest/TCA
adapters remain explicitly `NOT_TESTED` when the required evidence is absent.
Existing paper lineage does not prove a fill or a reconciled account.

Each displayed model claim must cite an allowed frozen hash. The host validates
ownership, contract, snapshot, creation/availability time and analyst lineage on
reload. News inputs must be `InstitutionDocument` records available by the frozen
snapshot time. Source text is untrusted data and cannot choose an agent's role,
capabilities or tools. Research opinions and source claims retain their provenance.
Citation ownership is a provenance check; a model interpretation still requires
independent factual review and is not predictive validation.

Local model calls are serialized, including across service instances. Compact support
roles and chat use a 20-second deadline and a 500-token output cap; Ollama is tightened
to 300 tokens, one short claim, and one grammar-constrained citation. Existing Bull/Bear
budgets remain bounded. A background transport that outlives its deadline retains the
transport slot until it exits; later roles record an unavailable result instead of
starting concurrent generations. Timeout, invalid JSON, foreign citations,
cancellation and unavailable providers freeze explicit abstention records. Cancelling
a cycle retains seven role records and a supervisor record.

All cycle, report and answer contracts have `execution_authority=false`. The service
has no order router, limit/permission setter, strategy editor or release authority.
NAYAK refuses requests to place orders or change permissions, limits or release
state. The existing deterministic portfolio, risk, paper/shadow, human review and
safety gates continue to own their responsibilities. A completed research cycle
does not establish trading readiness or profitability.

Validation covers all seven worker requests and supervisor consolidation, unavailable
adapters, foreign citations, structured execution fields, timeouts/failures,
cancellation, document injection/future availability, installed snapshot boundaries,
interactive answer citations/refusal, and immutable presentation state.

## Using the desktop desk

Open **Full Lab → AI Quant Desk → NAYAK / Institution**. The Three.js chamber is
enabled by default, with distinct figures for NAYAK, the Supervisor and all seven
specialists. Figure and roster selection expose the agent's status and frozen report;
native reports and chat remain available if the visual renderer is unavailable.
Load a frozen snapshot, and optionally point-in-time history or source documents.
Historical/synthetic inputs require **Explicit replay**. Select **Run institutional
desk**, then ask NAYAK a read-only question. Cancellation, inputs and questions are
serialized while a job is active. No cycle is started automatically on launch.

For the installed local model, configure `QUANT_LAB_AGENT_PROVIDER=ollama` and
`QUANT_LAB_OLLAMA_MODEL=qwen3:1.7b` in the local ignored `.env` file. The existing
default provider selection is unchanged for other installations. Native-only mode
is available with `QUANT_LAB_AGENT_VISUALS=0`.

The equivalent command is `quantlab institution run --snapshot PATH --replay`;
`quantlab institution history` lists verified cycles, and
`quantlab institution ask --cycle HASH --question "What evidence is missing?"`
creates a cited frozen answer.

## Local acceptance, 11 October 2026

The regression suite passed 1,660 tests; scoped lint, strict typing, frontend
typecheck and production bundle build passed. A real isolated Ollama/Qwen3:1.7b
cycle used a clearly labelled synthetic replay, not account or live market evidence.
After compact-response tuning, all five support roles, the Supervisor and NAYAK
returned schema-valid, owned-citation model reports. Bull and Bear plans ran, but
their larger memos reached the existing bounded deadline and retained explicit
`LOCAL_MEMO_TIMEOUT` abstentions. The cycle remained `ABSTAIN` with missing
validation, risk and reconciliation evidence, and a live-order question was refused.
The visible desktop chat was also exercised successfully against that frozen cycle.

This is software and local-model integration evidence. It is not independently
validated trading performance, completed paper/shadow acceptance, a reconciled
broker account, or authorization to trade. Source code is local; no remote push
is required to use the new desk.
