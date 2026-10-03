# Shadow Operations visual QA

## Comparison target

- Source visual truth: `/Users/vaibhavkumarn/.codex/generated_images/01a0f8ff-321f-7133-95a3-94b4f2930e66/exec-c5657a2d-16b9-4564-8d8c-9207c5166b07.png`
- Rendered implementation: `/tmp/quantlab-ui-qa/shadow-lab-final.png`
- State: dark theme, full-lab navigation, `Shadow Trading Lab`, no prior shadow cycle.
- Source pixels: 1487 × 1058. Implementation pixels: 960 × 800.
- Implementation CSS/window size: 960 × 800 at device scale factor 1, captured from the native Qt off-screen renderer. The source is a broader conceptual desktop reference, so this was reviewed for hierarchy, palette, density, and safety treatment rather than pixel-for-pixel geometry.

## Evidence

The source and rendered Shadow Trading Lab were provided together in one multi-image comparison input. The full views made the command bar, permanent safety band, navigation rail, empty-state framing, table treatment, and footer readable; no separate focused crop was needed.

## Required fidelity surfaces

- **Fonts and typography:** native system sans with a stronger hierarchy for page titles, cyan operational eyebrows, compact table headers, and legible safety copy. The source's condensed display type is not copied because it is not a project asset; the native fallback remains clear at the 960 px minimum width.
- **Spacing and layout rhythm:** shared header, rail, breadcrumb, safety ribbon, glass cards, and status footer preserve a consistent vertical rhythm. Every standard lab page now enters through the same `LabPageShell` surface.
- **Colors and visual tokens:** deep navy canvases, cyan telemetry accents, amber simulation warnings, and red live-danger treatment reproduce the chosen direction while retaining the product's own safety semantics.
- **Image quality and asset fidelity:** no source artwork, logo, illustration, or non-standard icon was copied or approximated. The target direction is conveyed through native Qt panels, tables, and actual chart renderers.
- **Copy and content:** the app keeps truthful product copy. The empty diagnostics and shadow-cycle state are deliberately not replaced by fabricated market ticks, fills, positions, or incidents.

## Comparison history

1. **P1 — header crowding at minimum desktop width.** The initial rendered home capture let the assistant-status line compete with the command surface. Fixed by removing the duplicate header status line while keeping it in the home workspace; revised evidence: `/tmp/quantlab-ui-qa/shadow-operations-final.png`.
2. **Post-fix comparison.** The command surface, safety ribbon, mode controls, and version tag remain distinct at 960 × 800. The matching Shadow Trading Lab capture confirms the shared glass system applies beyond the home page.

## Findings

No actionable P0, P1, or P2 visual differences remain for the adapted native-desktop implementation.

- **Accepted intentional difference:** the reference presents a populated operations dashboard, while the app renders its genuine empty shadow state until the user runs a cycle. This protects data integrity and avoids implying a live broker or market connection.
- **P3 follow-up:** once genuine shadow diagnostics exist, the existing table and chart widgets will automatically make the operations page denser; a future data-backed inspector can add more of the reference's incident-detail depth without changing the shared visual system.

## Implementation checklist

- [x] Shared glass surfaces across shell, nav, controls, tables, tabs, cards, notifications, and footer.
- [x] Persistent research/shadow safety ribbon with explicit disabled live and broker-write state.
- [x] Command surface and responsive top-bar treatment.
- [x] Dark and light themes updated as one visual system.
- [x] Native rendered captures and full UI test suite validated.

final result: passed
