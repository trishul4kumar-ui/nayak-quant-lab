# Interaction and terminal workspace remediation — 2026-10-03

## Scope

This review covered the native PySide6 desktop suite using the user-provided screens of Home, Data Fabric, Backtest Lab, Portfolio Lab, Experiment Ledger, and System. It also used fresh off-screen renders of Data Fabric and Backtest Lab after the changes.

## Confirmed issues

1. Most lab pages used fixed `QVBoxLayout` stacks. Existing splitters were limited to a few data-heavy pages, and their handles were nearly invisible.
2. Panel expansion used a glyph-only control with no restore state or clear visual response.
3. Several controls were enabled despite lacking valid input or an eligible selection. Clicking them could return with no visible response.
4. Tables supported selection but did not consistently advertise professional terminal-style column adjustment.

## Implemented remediation

- Every standard `LabPageShell` now finalizes into a persisted vertical terminal workspace with visible 8 px drag handles and a `Reset panels` control.
- Home has a persisted journal/pulse splitter; Journal retains a persisted list/detail splitter.
- Existing terminal panels use an explicit `Focus` / `Restore` control instead of a font-dependent glyph. Focus is reversible and layout state saves automatically.
- Table headers can be reordered, the final column stretches, and widths remain user-adjustable.
- All enabled initial controls acknowledge clicks in the terminal status rail.
- Input-dependent controls are disabled until actionable: AI Send, journal note saving, quick note saving, Compare selected, and settings-name Save.
- The Research page now contains resizable research-brief and next-action panels rather than a static narrative-only surface.

## Validation

- `tests/ui/test_terminal_workspaces.py` verifies all registered pages are selectable, every lab page has terminal resizing support, focus restores correctly, and enabled controls have feedback wiring.
- Existing UI tests continue to cover command palette, theme, data tables, jobs, and page-specific workflows.

## Evidence limits

- The audit verifies UI behavior with isolated local runtime data. It does not represent a broker connection, live market feed, live order capability, or profitability.
- A disabled control is intentional when its required state does not exist; the remediation makes that state explicit rather than allowing a silent no-op.
