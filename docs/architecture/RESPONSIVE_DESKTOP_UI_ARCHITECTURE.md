# Responsive desktop UI architecture

QUANT LAB is a native desktop scientific workstation. The responsive system uses
logical **page content** width, so a MacBook, Retina display, and external
monitor behave consistently without assumptions about physical pixels.

## Viewport policy

| Content width | Layout policy |
| --- | --- |
| `< 1100` | Compact desktop: icon sidebar rail, two/one KPI cards, one terminal column, stacked master/detail and toolbar actions |
| `1100–1439` | Standard desktop: saved sidebar preference, up to four KPI cards, two terminal columns |
| `1440–1919` | Wide desktop: expanded workspace, four KPI cards, two terminal columns |
| `>= 1920` | Ultrawide: optional three terminal columns where the page requests them |

`quantlab.ui.responsive.ResponsiveState` is the single source of these decisions.
`MainWindow` debounces resize events and distributes the resolved state to page
shells and responsive components. Preferences are not overwritten when an icon
rail is temporarily required by a narrow window.

## Shared components

- `LabPageShell` keeps title/status and actions in separate responsive rows.
- `DashboardStrip` wraps cards at usable card widths; it does not reduce text.
- `TerminalGrid` changes its column count at a viewport boundary, preserves
  panel content, validates restored ratios, and does not persist temporary focus.
- `ResearchTable` uses interactive/reorderable columns with predictable width
  contracts and local horizontal scrolling when a dense surface needs it.
- `wrap_page_scroll` allows horizontal overflow when a page cannot safely
  reflow, rather than silently clipping it.

## Recovery and persistence

`UiSettings.ui_layout_schema_version` is `2`. A layout from another schema is
discarded. Restored splitter arrays must match the live splitter count, have
usable minimum values, and may not contain near-zero panels. The **Reset
workspace layout** command clears only UI layout state; it never deletes
research data, experiments, journals, artifacts, or credentials.

## MacBook first

The acceptance targets are 1024×640 (usable), 1280×800 (fully usable), and
1512×982 (comfortable). Dense tables may scroll locally. Charts retain usable
heights; a compact page reflows before anything is forced into a narrow sliver.
