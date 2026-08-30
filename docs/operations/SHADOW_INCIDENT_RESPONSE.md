# Shadow Incident Response

**Version:** 2.4.0

Incidents (`DATA_STALE`, `CALENDAR_UNKNOWN`, `RECONCILIATION_BREAK`, `CHECKPOINT_CORRUPTION`, `CERTIFICATION_EXPIRED`, …) are retained. They are not deleted.

Unknown calendar is never treated as OPEN. Stale data cannot generate a trade decision. A live route attempt is FAIL plus safety HALT.

AI content is `AI_SUGGESTION` and cannot disable kill switches, change certification, or place orders.
