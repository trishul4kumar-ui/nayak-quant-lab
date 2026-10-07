# Intraday data and latency contract

Each observation records provider/exchange/last-trade timestamps when supplied, plus local
receipt and processing times. A provider sequence is optional and is never fabricated.
Duplicate, out-of-order, gap, stale, and missing-depth conditions are first-class states.
No future tick is available to replay or feature calculation.
