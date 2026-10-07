# Daily desk runbook

1. Configure a versioned `SourcedCalendar` from an approved exchange-session source.
   Do not start the desk with the weekday fallback.
2. Start or resume a daily desk with that calendar and the bounded `49-v1` policy.
   The scheduler returns a finite job list; a caller must persist outcomes before a
   later tick considers new work.
3. During opening, invalidate stale pre-market candidates and refresh required
   research evidence. Do not reuse pre-market levels after material price movement.
4. Review only fresh validated `ACTION_REQUIRED` candidates in Trade Queue.
   Notifications do not convey order authority.
5. On restart, run recovery before dispatch. It never duplicates completed jobs or
   silently replays a state-changing operation.
6. Use **Pause AI research** to halt new research work. It does not alter broker,
   paper/shadow, safety, or human execution controls. Resume requires a currently
   configured sourced calendar.

If persistence, calendar provenance, source quality, or bounded budgets cannot be
verified, keep the desk inactive/degraded and investigate rather than fabricating a
session, snapshot, or candidate.
