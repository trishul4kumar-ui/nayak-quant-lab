# Desktop Interaction Audit — 2026-10-03

## Scope

This audit ran the real PySide6 application under the Qt event loop with an
isolated local runtime. It did not mock button slots or call page actions
directly. Live trading and broker writes remained disabled throughout.

## Remediation shipped

- Every `LabPageShell` now has a compact, page-local action rail. A button
  click is acknowledged in the active workspace as `ACK · <ACTION>` before
  returning to `READY`; the footer remains a secondary status surface.
- Every completed lab page has a persisted, draggable vertical workspace
  splitter, plus an explicit `Reset panels` control. Nested terminal grids and
  the Journal detail splitter retain their own resize state.
- Terminal panel controls use an explicit `Focus` / `Restore` label rather
  than a glyph-only action.
- Incomplete actions are disabled until they can do useful work: AI send,
  journal/backtest note saves, selected-run compare, and settings save.
- Table headers are movable and retain the final column width, which makes
  dense research tables usable as terminal views rather than fixed reports.

## Executed interaction path

`tests/ui/test_institutional_interaction_audit.py` drives these interactions
with `QTest` mouse and keyboard events:

1. sidebar click opens Data fabric;
2. Technical details expands and receives a page-local acknowledgement;
3. a Data fabric tab changes the active dataset panel;
4. command search opens the modal palette and navigates to Backtest Lab;
5. Run backtest queues and completes a synthetic, next-bar-only job;
6. Compare selected renders the generated run;
7. Focus / Restore changes and restores a terminal panel;
8. Settings Save becomes enabled only after a changed name and persists it;
9. AI Research receives and answers a local research question;
10. safety assertions confirm `live_trading == false` and
    `broker_write_enabled == false`.

## Evidence and limits

- Runtime control sweep: no enabled `QPushButton` or `QToolButton` in the Full
  Lab window lacked a `clicked` receiver. The global acknowledgement receiver
  guarantees visible input feedback; it does not replace the page-specific
  behavioural contract above.
- Current offscreen render captures were reviewed for Data fabric and
  Backtest Lab. They show the compact action rail, explicit terminal controls,
  draggable panel divisions, and a consistent safety ribbon.
- This validates UI behaviour and the synthetic research workflow. It does not
  validate alpha quality, production market-data coverage, broker integration,
  or authorization for real orders.
