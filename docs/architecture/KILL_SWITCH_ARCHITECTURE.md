# Kill-switch architecture

Scopes: `GLOBAL`, `ACCOUNT`, `STRATEGY`, `SYMBOL`, `BUY`, `SELL`, `NEW_ORDER`, `MODIFY_ORDER`, `CANCEL_ORDER`, `LIVE_RELEASE`.

Activation is fail-safe. `LIVE_RELEASE_KILL` defaults **on** while `LIVE_TRADING=false` and cannot be cleared. A kill switch may block trading but never creates an order.
