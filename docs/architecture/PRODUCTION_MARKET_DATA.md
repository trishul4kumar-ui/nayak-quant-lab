# Production Market Data

**Version:** 2.1.0  
**ADR:** ADR-034

The existing PIT fabric (`available_time <= as_of`) is preserved.

Approved contract:

```python
from quantlab.data.market_data import get
get(security_id=..., start=..., end=..., as_of=...)
```

Raw bytes are copied once and checksummed. Tickers are labels. `symbol_at(security_id, T)` is historical. Official NSE holidays, NIFTY membership, and bid/ask history remain `NOT_TESTED` until sourced.
