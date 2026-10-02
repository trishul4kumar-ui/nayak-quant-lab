# QUANT LAB — PROMPT 33
# Institutional Live Account Reconciliation & Broker State Integrity Engine

**Target Version:** 3.3.0 | **Package:** `quantlab.reconciliation` | **ADR:** ADR-047

## Mission
Compare Prompt 32 broker observations with QUANT LAB internal state and answer:

> Does QUANT LAB's understanding of cash, positions, holdings, orders, fills and exposure agree with the broker?

```text
RECONCILE ≠ REPAIR
MISMATCH ≠ ORDER
BROKER OBSERVATION ≠ AUTHORIZATION
```

## Architecture
```text
Kite Read-Only → Broker Snapshot → Reconciliation
                                      ↑
                             QUANT LAB State
```

Do not create compensating orders.

## Dimensions
Reconcile:
- account identity
- cash/margins
- holdings
- positions/quantities
- average prices
- market value
- open orders/status
- trades/fills
- realized P&L where available
- timestamps
- canonical security identity

## States
```text
MATCH
MATCH_WITH_TOLERANCE
MISMATCH
UNKNOWN
STALE
BROKER_UNAVAILABLE
INTERNAL_STATE_UNAVAILABLE
RECONCILIATION_BREAK
```
`UNKNOWN` never becomes MATCH.

## Tolerances
All quantity, price, cash and timestamp tolerances must be explicit, versioned and recorded. No arbitrary hidden rounding.

## Identity
Map broker instruments through Prompt 20 security-master history. Ambiguity becomes `UNRESOLVED`.

## Order Reconciliation
Classify:
```text
MATCHED
BROKER_ONLY
INTERNAL_ONLY
STATUS_MISMATCH
QUANTITY_MISMATCH
PRICE_MISMATCH
TIMESTAMP_MISMATCH
UNKNOWN
```

## Fill Reconciliation
Use broker trade/fill identifiers. Matching price and quantity alone does not prove identity. Unknown fills become incidents.

## Immutable Report
Create `ReconciliationReport`:
```text
reconciliation_id
broker_snapshot_id
internal_snapshot_id
policy_version
tolerances
status
exceptions
reconciliation_hash
observed_at
```

## Exception State Machine
```text
OPEN → ACKNOWLEDGED → INVESTIGATING → EXPLAINED/RESOLVED
                                   ↘ ESCALATED
```
Original discrepancies are immutable.

## Safety
Critical mismatches may force `DEGRADED`, `PAUSED` or `HALTED` according to policy. Never generate an order.

## CLI
```bash
quantlab reconcile run
quantlab reconcile status
quantlab reconcile account
quantlab reconcile positions
quantlab reconcile orders
quantlab reconcile fills
quantlab reconcile cash
quantlab reconcile exceptions
quantlab reconcile history
quantlab reconcile report
quantlab reconcile audit
```

## Desktop
Create Account Reconciliation Lab showing broker/internal state, matches, mismatches, tolerances, incidents and hashes. No trade controls.

## Integrity
```text
reconciliation_snapshot_mismatch
broker_only_order
internal_only_order
unknown_fill
position_quantity_mismatch
cash_reconciliation_break
identity_mapping_mismatch
tolerance_override
hidden_reconciliation_exception
historical_reconciliation_mutation
stale_broker_snapshot
duplicate_broker_trade
duplicate_broker_order
```

## Testing
Test exact matches, tolerance boundaries, cash/position/order/fill mismatches, broker-only/internal-only records, duplicate fills, stale snapshots, identity failures, exception lifecycle, deterministic hashes and absence of compensating orders.

## Acceptance
Continuous broker-vs-internal reconciliation must be auditable, deterministic and incapable of turning discrepancies into trading actions.

```text
LIVE_TRADING=false
BROKER_WRITE_ENABLED=false
```
