# UI system pre-remediation baseline — 2026-10-04

## Verified environment

- Branch: `main`
- Package version: `3.1.0`
- Python: `3.12.4`
- Qt: `6.11.2`
- Safety defaults: `LIVE_TRADING=false`, `BROKER_WRITE_ENABLED=false`
- Kite integration: read-only REST quote observation; no order endpoint added

## Confirmed root causes

The prior UI hid page-level horizontal overflow, forced every `LabPageShell`
into a vertical splitter workspace, used static terminal-grid columns, kept KPI
cards in a single row, and restored raw splitter pixel ratios without validating
them against current screen size. This explains squeezed cards, chart slivers,
and clipped/awkward action rows on MacBook-class displays.

## Baseline verification

Ruff and mypy passed before the responsive changes. A full pytest run was
started; local disk exhaustion interrupted its final output. The cache was then
cleared and the focused UI suite was rerun during remediation.
