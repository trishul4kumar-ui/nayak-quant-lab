# Responsive visual QA — 2026-10-04

Offscreen Qt renders were inspected after the remediation at 1024×640,
1280×800, and 1512×982. The app was run in Full Lab, dark theme, using a fresh
local runtime directory.

| Page | 1024×640 | 1280×800 | 1512×982 | Result |
| --- | --- | --- | --- | --- |
| Home | icon rail, two-column KPI cards, scrollable content | readable | comfortable | pass |
| Backtest | action row stacks and form remains readable | KPI cards wrap | terminal workspace has room | pass |
| Validation | primary action visible, single-column evidence begins below fold | readable terminal panel | comfortable | pass |
| Portfolio | compact reflow avoids side-by-side chart/table squeeze | readable | table has usable columns | pass |
| Risk | KPI cards wrap and chart has a usable rectangle | readable | comfortable | pass |
| Real-Time Data | read-only controls and state stay visible | readable | comfortable | pass |
| Reconciliation | dense table retains local scroll capacity and empty state remains actionable | readable | comfortable | pass |

The checks are visual evidence for the listed rendered states, not proof that
every data condition or every display/DPI combination has been manually tested.
