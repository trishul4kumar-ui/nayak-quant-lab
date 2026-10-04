# UI component contract

All new PySide6 pages must use the shared responsive state rather than adding
page-local width breakpoints.

## LabPageShell

Use it for page title, subtitle, safety/context note, status acknowledgement,
and action row. `enable_terminal_layout()` is opt-in for genuinely resizable
workspaces; catalog and flowing evidence pages must not be nested into a
splitter merely because they share the shell.

## DashboardStrip

KPI cards have a usable minimum width and wrap between four, three, two, and
one columns. Never make KPI typography smaller simply to keep one row.

## TerminalGrid and TerminalPanel

Use a `TerminalGrid` for related dense panels that benefit from direct resizing.
Panels must declare a usable minimum width where their data is dense. Focus is
temporary and Restore returns the exact pre-focus ratios. Persisted ratios are
schema- and count-validated before use.

## ResearchTable

Use `fill_table` for tables. It applies stable widths, interactive/reorderable
headers, per-cell full-value tooltips, semantic alignment, and local scrollbars.
Do not call `resizeColumnsToContents()` on every refresh.

## Responsive action and evidence layouts

Primary actions remain visible. On compact desktop, secondary actions stack;
pages may use a menu for further actions. Chart/table pairs stack before either
side is narrowed below a useful research width.
