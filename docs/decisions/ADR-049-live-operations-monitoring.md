# ADR-049 — Live Operations Monitoring and Incident Response

## Context

Prompt 38 needs operations visibility and containment without granting any
monitoring component trading, remediation, or automatic-resume authority.

## Decision

Add `quantlab.live_ops` with typed health signals, deduplicated alerts,
append-only incident transition events, evidence, and idempotent safe actions.
Critical alerts request human investigation by default; a policy may invoke the
existing global kill switch, but never resumes a subsystem.

## Consequences

- Missing data and reconciliation evidence remain `UNKNOWN`, never healthy by
  assumption.
- Human acknowledgement and resolution reject AI/system actors and require
  rationale; resolution also requires evidence.
- Operations actions never create or modify orders, positions, or strategies.
