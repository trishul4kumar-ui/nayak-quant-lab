# Phase 40 — Bull analyst

Built after Phase 39's published CI acceptance. Release acceptance is pending the
Phase 40 local/cloud gates; the build program records the current result.

Implemented a persistent, cancellable, research-only worker with the specified
state pipeline, immutable screen and plan, canonical feature ranks, compulsory
factor/regime/statistics/model/ensemble/validation/TCA requests, bounded optional
tools, self-falsification, strict memo drafts and hash-verified evidence references.
The model cannot select its own evidence statuses or attach foreign-run references.
Missing validation or cost evidence cannot become an actionable long conclusion.

Added existing-engine adapters for equal-weight universe beta and descriptive
market regime state. These are not NIFTY beta, residual alpha, factor attribution,
forecasts or validated predictive edge. Unsupported factor/regime analysis names
fail rather than being silently mapped. Statistics/model/ensemble/validation/TCA
adapters still need complete typed research inputs and remain explicitly unavailable;
the memo records these as `NOT_TESTED`, not synthetic PASS results.

The native Bull workspace has resizable supporting/contradicting evidence panels,
memo, raw confidence, uncertainties, all seven challenges, real state/tool timeline,
searchable history and working evidence navigation. Background jobs keep model calls
off the GUI thread. Optional visuals receive real states/completed-tool counts and
only the current run's confidence. Bear remains a separate foundation inspector.

Existing hashed Phase 39 contracts were preserved. New artifact types and a durable
run-claim namespace use the existing migrated SQLite control plane; no destructive
migration or in-memory fallback was added. Local provider configuration now reads
the application's `.env` pattern with secret-typed credentials.

Regression coverage includes NO_TRADE, missing validation, beta explanation risk,
stale-before-freeze, live-tool/sizing/order-price/prose-price rejection, foreign
references, required challenges, restart, atomic cross-instance claims, repeat
fixture screening, private configuration, size bounds and native button/history/
evidence navigation. Test providers exist only in tests. No real model or broker
request was used as validation, and no trading safety flag was enabled.

The OpenAI Docs skill informed strict structured-output schemas and explicit
refusal/incomplete handling. See BULL_MANDATE.md for the operating and token budgets.

## Verification

- Initial full regression: 1,477 passed in 488.96 seconds. Final small concurrency,
  CLI-exit, layout-persistence and effective-time guards are additionally regression
  tested; the exact final checkout is being checked locally and in published CI.
- Native desktop run completed `NO_TRADE` using a clearly labelled synthetic fixture;
  the rendered evidence/memo workspace was inspected at 1280×800.
- Source distribution and wheel built; final distribution packaging is also in CI.
- No real provider/broker request, live order, approval or safety-flag change occurred.
