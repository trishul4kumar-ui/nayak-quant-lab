# Reconciliation comparison integrity

The reconciliation service rejects empty or duplicate position, holding and order
identifiers rather than allowing a dictionary conversion to overwrite rows. A
duplicate security may represent separate products or accounts; the current
contract cannot disambiguate them, so the comparison reports a critical break
instead of merging them. Non-finite scalar values also create critical breaks.

Orders require a present status, positive finite quantity, present positive finite
price and timezone-aware timestamp before they can match. When a provider uses a
zero or absent price for a market order, the price is treated as unknown and the
report cannot claim a full match. Differences that fall within the explicitly
recorded tolerances are reported as tolerated rather than exact matches.

This is synthetic-test evidence for comparison logic, not independent account
reconciliation. The internal order schema does not yet include instrument,
side, order type, filled quantity or pending quantity; these are not compared.

Freshness policy version 3.6.0 additionally checks that broker source/capture
and internal observation timestamps are timezone-aware, no later than the
comparison cutoff, and no more than the configured maximum snapshot age before
it. Capture windows with missing, reversed or excessively separated endpoints
are stale. The default maximum age is 60 seconds and is part of the recorded
comparison policy. The application uses its actual comparison time for normal
non-fixture runs; test-fixture runs use the recorded capture time for deterministic
historical comparison. The low-level `reconcile` function also uses the recorded
capture time when no cutoff is supplied, so callers must provide an explicit
current cutoff to claim freshness at a current decision time.

Reports now bind a hash of the complete supplied broker bundle and internal book
alongside their identifiers. This prevents different content under the same IDs
from producing the same comparison identity. The hashes are not a digital
signature or proof that the two books are independent. The in-memory report
repository's `get("last")` lookup no longer attempts to acquire its lock twice.
