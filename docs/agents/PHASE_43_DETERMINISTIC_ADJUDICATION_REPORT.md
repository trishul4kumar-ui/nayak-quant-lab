# Phase 43 — Deterministic adjudication

Started after Phase 42's exact published CI acceptance for `167d8d4` in
[run 37199102925](https://github.com/trishul4kumar-ui/nayak-quant-lab/actions/runs/37199102925).
Release checks are in progress; Phase 44 must wait for this phase's cloud gate.

Implemented frozen canonical measurements, role evidence, typed research-gate
evidence, a registered immutable weighted policy, frozen evaluation inputs,
explainable decisions and a pure scoring function. No judge LLM, narrative
sentiment, agent confidence or authority over orders enters the final function.
The existing research gate is reused rather than replaced with agent judgment.

The native Adjudication workspace shows neutral component bars, canonical statuses,
scores, all blockers/warnings, policy and source identities, immutable history and
explicit NO_TRADE. Its splitter is user-resizable and persisted. The optional local
visual center mirrors the result and opens the verified native decision; its
read-only bridge rejects unpublished identities and execution intents. Native text
continues to work without WebEngine.

CLI: `quantlab agents adjudicate --transcript HASH` and
`quantlab agents adjudication-history`. The former returns status 2 for abstention
and status 0 only for further research processing; neither authorizes execution.
Hash/ancestry/policy verification runs on history retrieval and after restart.

## Verification

- Exact local full regression: **1,547 passed in 488.98 seconds**. Focused agent,
  terminal-workspace and layout suite: **139 passed in 27.66 seconds**. Optimized
  safety suite: **271 passed in 15.77 seconds**, with pytest's expected Python `-O`
  assertion warning. No cloud acceptance is claimed yet.
- Ruff and strict mypy passed (838 source files). TypeScript typecheck and locked
  production visual build passed; production dependency audit found 0 vulnerabilities.
  Optional local Three.js framework bundle: 537.43 KB minified / 134.92 KB gzip;
  Vite's size warning remains, with no continuous animation loop.
- Source/wheel built. Verified the adjudication modules, native widget and updated
  local HTML/JS/CSS plus third-party notice inside the wheel. Tracked secret scan
  and diff checks passed. No new SQLite schema is required; artifacts use the
  existing migrated append-only control plane. Prior memo contracts/hashes are unchanged.
- Tests cover deterministic serialization, changed policy identities, immutability,
  failed/stale/missing inputs, edge/cost and liquidity/risk blockers, ties, low scores,
  both dominance branches, synthetic/replay abstention, forbidden authority/quantity,
  re-sealed score/input/policy forgeries, narrative restyling, CLI and restart.
- Native Chromium interaction rendered 20 component bars and the exact native
  `INSUFFICIENT_DATA / NO_TRADE` result with 49 blockers. An actual pointer click on
  the center opened the native Adjudication tab. Two initials plus bounded critiques
  used six fixture calls; evaluation itself used **zero** model calls. The initial
  QA sampled Chromium before its asynchronous presentation update; polling the
  published state corrected the harness without a production-code change.
- Native fallback/navigation inspected at 1024×640, 1280×800, 1512×982 and 1920×1080
  in the headless suite. The actual Mac screenshot remains a display-clamped native
  check, not proof of an external-monitor setup. Panel preferences persist.

## Honest limitation

The existing agent tool bindings cannot yet supply the complete canonical metric
set. Actual desk evaluations remain blocked/no-trade with visible NOT_TESTED
components. Fixture dominance tests verify algorithm branches, **not** a tradable
strategy, sustained production shadow, real liquidity or profitability.
Calibration remains unavailable/zero-weight until Phase 48. No live order, paid
model request, safety-flag change or automatic approval is part of verification.

See ADJUDICATION_POLICY_SPEC.md for exact units, routes, weights and blocker precedence.
