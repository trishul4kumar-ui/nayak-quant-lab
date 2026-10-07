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
| 40 Bull | Accepted | CI green for `6aa8651`; 1,482 local tests passed |
| 41 Bear | Accepted | CI green for `794b880`; 1,499 local tests passed |
| 42 Debate | Accepted | CI green for `167d8d4`; 1,517 local tests passed |
| 43 Adjudication | Accepted | CI green for `99e506d` |
| 44 Levels | Accepted | CI green for `960b7af` |
| 45 Candidates | Accepted | CI green for `20192f7` |
| 46 Console | Accepted | CI green for `20192f7` |
| 47 Position review | Accepted | CI green for `20192f7` |
| 48 Calibration | Accepted | CI green for `20192f7` |
| 49 Daily desk | In progress | Consolidated local verification and CI after Phase 45–48 acceptance |
| 50 Intraday | In progress | Deterministic replay, cost/risk evidence, consolidated verification |
| 51 Paper | In progress | Candidate lineage through canonical Paper OMS |
| 52 Production shadow | In progress | Sustained real observations and zero-write evidence |
| 53 Human execution | Implemented — evidence dossier only; live blocked | All prior gates, sustained shadow, certified authorization, secure gateway deployment |

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
Phase 40 began only after this result. At foundation acceptance, Phases 41–53 remained pending; phase 53
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

The accepted foundation is not an end-to-end trading strategy. See
AGENT_TOOL_CATALOG.md before using tool names as evidence.

## Bull acceptance and Bear progression

Phase 40 passed all published gates for `6aa8651` in
[CI run 37177882546](https://github.com/trishul4kumar-ui/nayak-quant-lab/actions/runs/37177882546).
The exact local checkout passed **1,482 tests in 402.73 seconds**, Ruff, and strict
mypy across 829 source files. Phase 41 began only after the cloud result was green.
It adds an independent Bear mandate/memo and mirrored native workspace on the same
bounded worker infrastructure; missing instrument eligibility stays UNKNOWN.
Phase 42 cannot begin until Phase 41's release checks also pass.

Phase 41's release checks passed for `794b880` in
[CI run 37196120100](https://github.com/trishul4kumar-ui/nayak-quant-lab/actions/runs/37196120100).
The exact local checkout passed **1,499 tests in 423.65 seconds**, plus 223
optimized-mode safety tests, Ruff, strict mypy and source/wheel builds. Phase 42
began after this acceptance. Phase 42's release checks then passed for `167d8d4` in
[CI run 37199102925](https://github.com/trishul4kumar-ui/nayak-quant-lab/actions/runs/37199102925).
The exact local checkout passed **1,517 tests in 475.36 seconds**. Phase 43 began
only after that cloud acceptance. Phase 44 remains pending its adjudication release gate.

## Phase 44 acceptance and 45–48 local batch

Phase 44 passed its cloud release gate for `960b7af` in
[CI run 37613631593](https://github.com/trishul4kumar-ui/nayak-quant-lab/actions/runs/37613631593)
on 2026-10-07. The agreed implementation workflow now batches the dependent
research-only Phases 45–48 in one local change set, with focused checks during
implementation and a single consolidated local/CI release gate at the end.
This reduces publication overhead but does not waive any evidence gate. Until that
future gate is green, Phases 45–48 remain in progress and cannot support Phase 49
or any order-routing capability.

## Phase 45–48 acceptance and Phase 49 progression

The batched Phase 45–48 change set passed its cloud release gate for `20192f7` in
[CI run 37668583689](https://github.com/trishul4kumar-ui/nayak-quant-lab/actions/runs/37668583689)
on 2026-10-08. The run passed visual build, Ruff, strict mypy, secret-pattern scan,
optimized safety coverage, the complete coverage suite, and distribution build. Phase
49 may now proceed as a research/paper-only orchestration phase; it inherits all prior
fail-closed and human-execution boundaries.

## Phase 43 acceptance and Phase 44 progression

Phase 43's release gate passed for `99e506d` in
[CI run 37609867338](https://github.com/trishul4kumar-ui/nayak-quant-lab/actions/runs/37609867338)
on 2026-10-07. The metadata-only commit triggered the repository's existing
push workflow without changing Phase 43 source files. The exact clean checkout
also passed the complete local suite, focused adjudication tests, Ruff, strict
mypy and optimized safety suite. Phase 44 then began. Its cloud acceptance is
not claimed until its own change set passes CI; Phase 45 remains pending.
