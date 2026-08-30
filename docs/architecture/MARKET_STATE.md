# Market state

**Status:** Prompt 09 (2026-08-30) — ADR-010 + ADR-023  
**Packages:** `quantlab.market.state` (per-instrument), `quantlab.regimes.snapshot` (cross-section)

QUANT LAB has two state objects. They are not interchangeable.

| Object | Scope | Package | Role |
|---|---|---|---|
| `MarketState` (ADR-010) | One instrument at T | `quantlab.domain.models` / `quantlab.market.state` | Price, volume, name-level features (`momentum_20`, …) |
| `StateSnapshot` (ADR-023) | Cross-section at T | `quantlab.regimes.snapshot` | Equal-weight universe observables |

A snapshot **describes** observable market conditions. It is not a forecast, not a regime label, and not alpha.

## Point-in-time

`StateSnapshot(T)` uses `available_time <= T` and `Universe(T)`. Appending later bars cannot change the snapshot at T. A name that only exists after T is not in `n_names` at T.

Missing fields are `None`, never silent zeros. `index_nifty_return` and `liquidity_adv` are always missing until a licensed index and calibrated ADV exist.

## Market return

`market_ew_return` is the cross-sectional mean of PIT simple close-to-close returns (`equal_weight_universe`). It is **not** NIFTY.

## Seed variables

Implemented from bundled bars: `market_ew_return`, `realized_vol_20`, `dispersion_cs`, `breadth_sign`, `avg_pairwise_corr`, `ew_drawdown`, `vol_velocity`.

`NOT_TESTED`: `index_nifty_return`, `liquidity_adv`. Official holidays remain unsourced.

## Normalization

Expanding and rolling z-scores, and expanding terciles, end their window at T. Full-sample z-scores are not used as historical features.

`quantlab state list|inspect|compute`
