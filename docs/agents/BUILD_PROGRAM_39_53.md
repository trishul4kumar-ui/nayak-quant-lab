# AI Quant Desk build program

Source: `QUANT_LAB_AI_QUANT_DESK_CODEX_PHASES_39_53`, supplied on 2026-10-04.
All six reference documents and all fifteen phase prompts were read before editing.
The implementation follows the supplied dependency order; a blocked gate is recorded,
never replaced with synthetic evidence or a completion claim.

## Existing baseline

- Existing changes in this checkout are preserved.
- Initial Ruff passed; strict mypy passed across 809 source files.
- Initial full suite: **1,405 passed, 2 failed**, in 401.89 seconds.
- Failures: sidebar search was hidden by compact layout; responsive terminal rebuilds
  registered duplicate focus handlers. Fixes and regression verification are included.
- Existing 01–38 risk register remains applicable: authorization, reconciliation,
  production-shadow and live-operations repositories still have durability debt.
  Research-only phase 39 does not depend on those stores; live promotion does.

## Gates

| Phase | Status | Next evidence required |
|---|---|---|
| 39 Foundation | Accepted | CI green for `3abef8f` |
| 40 Bull | Implemented; verification in progress | Local and published release gates |
| 41 Bear | Pending | Shared contracts and Bull accepted |
| 42 Debate | Pending | Independent frozen memos |
| 43 Adjudication | Pending | Bounded debate accepted |
| 44 Levels | Pending | Deterministic evidence decision |
| 45 Candidates | Pending | Complete immutable upstream lineage |
| 46 Console | Pending | Candidate lifecycle and responsive UI |
| 47 Position review | Pending | Paper/shadow position contracts |
| 48 Calibration | Pending | Time-bound outcome records |
| 49 Daily desk | Pending | Prior phases and source-backed exchange sessions |
| 50 Intraday | Pending | Replayable ticks and depth; deterministic cost/risk path |
| 51 Paper | Pending | Canonical paper OMS integration |
| 52 Production shadow | Pending | Sustained real observations and restart evidence |
| 53 Human execution | Blocked | All prior gates, sustained shadow, certified authorization, secure gateway deployment |

Local checks are evidence for this checkout only. GitHub CI is not reported as green
for unpublished changes. No commit, push, live broker submission, or remote deployment
is implied by this program.

## Publication and foundation acceptance

The supplied acceptance matrix expressly forbids progressing with `CI_RED`.
The initial published run for HEAD `7d9be18` was
[GitHub run 37127197785](https://github.com/trishul4kumar-ui/nayak-quant-lab/actions/runs/37127197785),
which failed UI test collection because `libEGL.so.1` was absent on the Linux runner.
The unpublished workflow includes Qt runtime installation, an import smoke check,
the locked visual build, and agent tests. That is a prepared fix, not a green cloud run.

Publication was authorized on 2026-10-04. Baseline/foundation commit `9a4e1b0`
was pushed, excluding credentials and runtime experiment data. Its
[CI run 37173447623](https://github.com/trishul4kumar-ui/nayak-quant-lab/actions/runs/37173447623)
passed Qt import, visual build, Ruff and mypy, then exposed two legacy covariance
failures on Linux: a numerically null eigenvalue rounded slightly positive and
triggered the ill-conditioning guard. The canonical fix uses a shared scale-aware
rank/invertibility threshold, preserves rejection of genuinely ill-scaled asset
variances, and tests both signs of null-eigenvalue roundoff. A fresh cloud gate is
required before Phase 40 begins.

The covariance rerun passed the full suite, but its optimized-mode selection
exposed test-order leakage: a preceding production-shadow test left failed
upstream evidence in process-global stores. The missing-evidence authorization
fixture now resets all its upstream stores. A separate regression asserts that
an actual global kill still produces `BLOCKED`; no production safety rule changed.

The next run passed both test suites and built distributions, then exposed broken
shell quoting in the legacy final secret check. The same tracked-file assignment
pattern now runs through a tested argument-list scanner; matching values are never
printed. Secret and optimized-mode checks now run before the long covered suite.

Foundation acceptance: all cloud gates passed for `3abef8f` in
[CI run 37175625914](https://github.com/trishul4kumar-ui/nayak-quant-lab/actions/runs/37175625914).
Phase 40 began only after this result. Phases 41–53 remain pending; phase 53
additionally requires the separately documented durability work,
sustained real production-shadow evidence, and explicit human execution controls.

## Local verification — 2026-10-04

- Final full regression run: **1,454 passed**, in **384.87 seconds**.
- Agent foundation and control-plane focused tests: **49 passed**.
- Optimized-mode agents/control-plane/safety/restricted-execution: **93 passed**;
  pytest emitted its expected warning about Python `-O` outside rewritten test modules.
- Ruff: passed. Strict mypy: passed, **824 source files**.
- All five agent CLI commands: successful JSON responses using isolated runtime data.
- TypeScript type check and Vite production build: passed. Production dependency
  audit: **0 vulnerabilities**. Vite notes the optional Three.js bundle is 528 KB
  minified (132 KB gzip); it is local, opt-in, and has no continuous animation loop.
- Wheel: built; local HTML/JS/CSS and the Three.js MIT notice verified inside it;
  no `node_modules` packaged. Build isolation was needed because Hatchling is
  not installed in the application virtual environment.
- Native Chromium check: WebChannel connected, WebGL canvas rendered, and clicking
  the Bear station selected the native Bear tab. Profile teardown warning resolved.
- Native main window: 1024×640 compact layout and a wide-window request clamped by
  the Mac display to 1440×842. Headless native inspectors also tested at
  1024×640, 1280×800, 1512×982, and 1920×1080. This is not an external-monitor pass.
- Corrupt/closed database, forged provenance, history boundary, missing WebEngine,
  unknown tools, denied grants, schema refusal, timeout, cancellation, and restart
  behavior covered. No model or live broker request was dispatched during validation.

The accepted foundation is not an end-to-end trading strategy. Phase 40 adds a
bounded Bull worker and two further canonical adapters; Bear and later desk phases
remain pending. See AGENT_TOOL_CATALOG.md before using tool names as evidence.
