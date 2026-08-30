# Market impact

Formulas (research, **UNCALIBRATED**):

- fixed bps
- square-root: `k × vol × sqrt(q/V)`
- participation: `k × q/V`

Missing volume or vol does not become silent 0 — impact is `NOT_TESTED` and is not applied as a calibrated zero.

No NSE/BSE calibration is claimed. Coefficients are scenario inputs.

CLI: `quantlab execution impact`.
