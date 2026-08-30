# QUANT LAB Target Architecture v0.2

**Status:** freeze candidate after Prompt 02 reconciliation (2026-08-30)  
**Does not replace** `QUANT_LAB_ARCHITECTURE.md` (Prompt 01). This is the expanded target.

## System context

Local-first scientific laboratory for Indian cash/derivatives. AI expands the search space. Mathematics and statistics decide whether evidence exists. The risk firewall decides what may be traded. Execution is a separate engine. Brokers are adapters.

```
OBSERVE → REPRESENT (MarketState) → HYPOTHESIS → EXPERIMENT
  → FALSIFY (integrity) → PORTFOLIO → RISK → EXECUTE → LEARN
```

## Domain model (v0.2)

Canonical objects: Instrument, MarketEvent, OHLCVBar, **MarketState**, Feature, Factor, **SignalGenome**, Signal, **ResearchHypothesis**, Alpha, Model/ModelVersion, Strategy, Portfolio, Position, TargetPosition, Order, Fill, Execution, RiskDecision, Experiment, **DataLineage**.

Signal ≠ forecast ≠ target position ≠ order ≠ fill.

## Component model

| Layer | Package | Authority |
|---|---|---|
| Data fabric | `quantlab.data` | Provider protocol, validation, PIT |
| Quant/math | `quantlab.math` | Deterministic primitives |
| Market representation | `quantlab.market` | MarketState builder |
| Research | `quantlab.research` | Features, genome eval, hypotheses, integrity |
| Models | `quantlab.models` | Lifecycle + ledger (no auto-live) |
| Portfolio | `quantlab.portfolio` | Optimizer protocol |
| Risk | `quantlab.risk` | Firewall + risk states |
| Backtest | `quantlab.backtest` | Next-bar, costs, metrics |
| Execution | `quantlab.execution` | OMS + reconciliation |
| Brokers | `quantlab.brokers` | Paper / future OpenAlgo / Zerodha |
| AI | `quantlab.ai` | Permissions only |
| Observability | `quantlab.observability` | Structured logs + audit |

## Data flow

Vendor/file/synthetic → normalize → validate → **MarketState** (as-of available_time) → features → genome → signals.

## Research flow

Hypothesis → SignalGenome → features → historical eval → integrity (PASS/WARN/FAIL/NOT_TESTED) → cost-adjusted backtest → metrics → ledger + lineage. Rejected ideas remain in the ledger.

## AI flow

Agents may read, propose hypotheses, and request experiments. They cannot bypass risk, change limits, or place live orders.

## Risk flow

Proposal → listed instrument → limits → **RiskState** (HALT/EMERGENCY reject all new exposure) → APPROVE/MODIFY/REJECT. Logged.

## Execution flow

CREATED → VALIDATING → RISK_PENDING → APPROVED|REJECTED → SUBMITTED → ACK → FILL. Live unreachable unless `LiveSafetyGates.all_pass()`. Uncertain broker state → no new live orders (reconciliation).

## Deployment

Still a single local process. Optional docker-compose Postgres/Redis. No cloud required for research.

## Security

Secrets only via environment. No credentials in git. Research artifacts treated as sensitive. Live default false.

## Observability

Events carry timestamp, component, event_type, correlation_id, and optional strategy/experiment/instrument ids. Audit sink for risk decisions.
