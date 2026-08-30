# Pre-Live Certification

**Version:** 2.3.0

State machine: `DRAFT → UNDER_VALIDATION → VALIDATION_PASSED|FAILED → PAPER_* → SHADOW_* → PRELIVE_REVIEW → CERTIFIED → SUSPENDED|RETIRED`.

Illegal transitions raise `IllegalCertificationTransition`. `DRAFT → CERTIFIED` is forbidden. `CERTIFIED` is not live trading and not broker permission. The future broker gateway is a separate program.
