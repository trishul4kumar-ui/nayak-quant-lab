# Liquidity and capacity

PIT session volume and trailing mean volume use bars with `available_time <= T`.

Synthetic `MemoryBarProvider` volume (`1_000_000 + 1000 * i`) is **not** official NSE ADV. Capacity remains `NOT_TESTED`.

Unknown volume (`exec_unknown_adv`) does not imply infinite liquidity — fills are unfilled and capacity is `NOT_TESTED`.

Notional scenarios: ₹1L, ₹10L, ₹50L, ₹1Cr, ₹5Cr, ₹10Cr. Report fill ratio, participation, partials, and cost/capital. Breaks are diagnostics, not a capacity certificate.

CLI: `quantlab execution liquidity|capacity` / `quantlab research capacity`.
