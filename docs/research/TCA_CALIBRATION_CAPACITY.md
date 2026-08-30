# TCA, Calibration & Capacity

**Version:** 2.1.0  
**ADR:** ADR-035

`quantlab.tca` wraps Prompt 13 models and Prompt 18 fills.

Implementation shortfall:

```
IS = delay + trading + spread + impact + opportunity + explicit fees
```

Observed, modelled, calibrated, and stressed TCA are distinct. Synthetic volume is not NSE ADV. Indian tax legs stay unspecified until sourced.
