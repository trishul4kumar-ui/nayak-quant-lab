# Prompt 01–38 remediation report — 2026-10-04

## Completed in this remediation

- Added a central responsive desktop policy and viewport-matrix tests.
- Reworked page/top-bar reflow, sidebar effective state, KPI wrapping, terminal
  grid reflow, focus/restore behavior, splitter validation, UI layout schema,
  and Reset workspace layout.
- Removed global implicit terminalization of all lab pages.
- Added shared research-table width, alignment, tooltip, header, and scroll
  policy.
- Rendered critical pages at MacBook and desktop dimensions.
- Installed Linux Qt/EGL runtime dependencies and offscreen mode in CI.
- Repaired the canonical backtest calendar to use the union of exchange session
  prints rather than an all-instrument date intersection.
- Removed automatic use of synthetic seed volume in TCA. Capacity stays
  `NOT_TESTED` unless typed liquidity evidence is supplied.

## Safety posture preserved

Kite remains REST/read-only observation. No broker-write adapter was introduced.
`LIVE_TRADING=false` and `BROKER_WRITE_ENABLED=false` remain the operating
defaults.
