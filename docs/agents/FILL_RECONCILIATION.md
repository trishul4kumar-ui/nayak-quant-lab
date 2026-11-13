# Fill reconciliation evidence

The existing reconciliation service compares each unique broker/internal fill ID,
order identity, quantity and price. Duplicates or conflicting identities and
out-of-tolerance quantities/prices produce critical breaks. Finite deviations
within the configured versioned tolerances are explicitly reported as tolerated,
not exact matches. Tolerance policy version 3.6.0 requires finite, non-negative
limits and is revalidated at the comparison boundary. Missing fills retain their
existing discrepancy statuses.

This comparison does not establish independent-account evidence by itself. Fill
timestamps, charges, currency, trading venue and instrument identity are not yet
compared; their semantics and availability require further source-contract work.
Tests use mock inputs and do not contact a broker.
