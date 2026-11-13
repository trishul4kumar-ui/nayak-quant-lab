# Explicit paper workflows

These are local, non-routable historical paper calculations. Real source facts do
not turn simulated fills into broker-confirmed executions, historical downloads
into independently verified PIT data, or research completion into validation.
No workflow modifies live gates or configures a broker execution gateway.

## Desktop sequence

1. Capture overlapping real closed-bar histories in Data Fabric. Run Portfolio
   research on an explicitly selected universe and inspect the resulting targets.
2. In Capital or Paper OMS, select that exact completed portfolio. Enter an
   explicit paper opening balance; this is not inferred from broker cash. Review
   the target and historical replay assumptions. Missing ADV remains unknown.
3. If appropriate for historical paper research, explicitly acknowledge missing
   ADV/PIT evidence. Without that acknowledgement capital abstains; no hidden
   unlimited-liquidity assumption is substituted. A five-percent minimum cash
   reserve and long-only/unlevered targets apply to constructor-budget allocation.
4. Prepare the reviewed immutable workflow, inspect its original target, cash and
   arrival marks, then run Paper OMS. Arrival must be strictly after the portfolio
   analytical cutoff; preparation uses the first common sourced closed-bar endpoint
   after it. Capture later history or select a portfolio with an earlier cutoff if
   none exists. Policy presets remain modeled assumptions.
5. Run modeled TCA against that workflow's original target and fills. Monitoring
   additionally requires a selected, strictly later capture covering all positions.
6. Shadow repeats the original non-routable historical inputs. Twin recomputes
   without using cached fill results and compares a selected published original source, target,
   reconciliation, cash and fill hashes/values. It does not re-date old facts as
   a fresh live observation. Replay received/available clocks are explicitly marked
   analytical assumptions; the actual source capture clock remains separate.

Portfolio rank scores are not calibrated expected returns. Constructor weights
can be budgeted directly; this path does not fabricate return forecasts or impose
an annual volatility target on unannualized per-interval covariance. Source
revisions, adjustments, membership, calendar validity and actual market-impact
calibration remain separately unverified capabilities.

## Background API

`ApplicationRuntime.submit_paper_workflow(parameters)` accepts these job kinds:

- `capital`: exact `research_result_hash`, positive `opening_cash`, explicit
  `allow_unverified_liquidity` boolean.
- `prepare`: the capital inputs plus `reviewed=true` and an
  `execution_policy_id` preset. An optional `arrival_history_hashes` selection must
  have the same named universe. Preparation returns a `workflow_id`.
- `paper_oms`, `tca`, `shadow`, `twin`: exact reviewed `workflow_id`.
- `monitoring`: exact `workflow_id` plus `mark_history_hashes` from a later capture.

TCA and monitoring may also specify `paper_result_hash` to pin the exact
published paper result; if specified, a missing or invalid result fails closed
instead of selecting another. Without it, their existing behavior selects the
most recently published paper result for the workflow.

Original inputs cite both exact published research and capital-allocation hashes.
Inputs and results are hash-addressed artifacts in the local control
plane. A result becomes consumable only after its experiment-ledger row and
completion audit publish successfully. Archived fixture records are not relabeled
as real, deleted or selected as fallback inputs.

Background cancellation is accepted until publication starts. Calculations do not
persist paper state, checkpoints or valuation marks before that boundary. Once
publication begins, late cancellation is rejected: success retains its complete
result, and a storage failure is reported as failed rather than cancelled.

## Restarting from a completed paper calculation

`restore_paper_checkpoint(repository, workflow_id, result_hash)` reopens the
exact completed historical paper inputs and result in a new process from the
canonical agent repository. It checks the artifact hashes and publication
identity, required result fields, order/fill counts and fill links, selected
paper identities, and source, research-context and capital references. TCA and
monitoring use this same verification before consuming a published result.
Restoration does not run the simulator, append fills, contact a broker, or grant
execution authority. The supplied hashes and the repository must be retained.

This is **not** restoration of a partially executed paper job, a continuously
running account, the separate in-memory digital twin, or a broker ledger. An
interrupted, unpublished result is unavailable. Hash checks detect inconsistent
or accidental corruption, but a local store an attacker can rewrite together
with its audit records is not independently authenticated. Source completeness
does not establish point-in-time correctness or profitability. Backups, durable
in-flight event checkpoints, operator recovery procedures, and independent
broker reconciliation remain separate work.

## Independent internal-book import

Reconciliation cannot create an internal book by copying a broker observation.
Import a JSON file under 1 MB that describes an independently maintained internal
account/event ledger. The top-level contract is:

```json
{
  "origin": "internal_event_ledger",
  "independently_maintained": true,
  "snapshot": {
    "snapshot_id": "your-independent-ledger-cutoff-id",
    "account_id_hash": "your-account-identity-hash",
    "observed_at": "2026-10-15T09:00:00+05:30",
    "available_cash": null,
    "utilized_margin": null,
    "available_margin": null,
    "holdings": [],
    "positions": [],
    "orders": [],
    "fills": []
  }
}
```

This is a schema example, not a usable statement of any account. Replace every
field with independently sourced facts; empty holdings mean explicitly no
holdings, not unknown holdings. Unknown balances remain null and cannot establish
agreement. `origin` may also be `operator_internal_book`; it must not be a broker
export or paper simulation. Never include credentials or raw authentication data.

Positions/holdings use `security_id`, `quantity`, and optional `average_price`,
`market_value`, `realized_pnl`. Orders use `broker_order_id`, `status`, `quantity`,
optional `price` and aware `observed_at`. Fills use `broker_fill_id`,
`broker_order_id`, `quantity`, `price`, optional aware `observed_at`.

Select the exact imported internal hash and independently captured broker bundle.
Account identity, source cutoff, capture window, mappings, quantities and balances
are checked under the displayed versioned tolerances. Missing internal state is
`INTERNAL_STATE_UNAVAILABLE`, never a fabricated match. Reconciliation records
differences; it does not repair books, place compensating orders or enable trading.
