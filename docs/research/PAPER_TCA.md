# Paper TCA

**Status:** Prompt 18 / ADR-032  
**Version:** 1.8.0

Paper TCA reports:

- gross target notional
- filled notional
- spread / slippage / impact drag
- commission
- other specified fees (unspecified Indian tax legs remain 0 / `NOT_TESTED`)
- total execution drag
- residual target

Implementation shortfall versus arrival snapshot price is computed only when arrival and execution prices are valid. Otherwise `NOT_TESTED`.

This is attribution of simulated paper fills. It is not a broker TCA tape.
