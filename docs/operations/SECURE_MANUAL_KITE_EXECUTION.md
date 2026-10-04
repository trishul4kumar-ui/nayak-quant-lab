# Secure manual Kite execution

## Boundary

The native QUANT LAB desktop is an order-ticket client. It never receives or
stores `KITE_API_SECRET`, and it never exchanges a Kite request token. A separately
deployed HTTPS gateway performs the Kite token exchange, keeps the access token in
process memory only, and makes the single order API request.

The gateway is intentionally narrow:

- one NSE cash (`CNC`) `LIMIT`, `DAY` order at a time;
- explicit server-side symbol allowlist and maximum notional;
- immutable order hash plus a typed `CONFIRM <hash>` phrase;
- a server-validated six-digit TOTP per submission window;
- idempotency is journaled before the Kite network call;
- timeout becomes `SUBMISSION_UNKNOWN`; it is never retried automatically;
- modify, cancel, market, AMO, basket, and automated orders are unsupported.

Kite accepts an order request before it can know whether that request is filled at
the exchange. Treat `ACKNOWLEDGED` as *request accepted*, then inspect the normal
read-only Broker Gateway for its actual state. [Kite order semantics](https://kite.trade/docs/connect/v3/orders/)

## Deploy the gateway

Deploy this as a **private server**, not on the Mac that runs QUANT LAB. Put it
behind an HTTPS reverse proxy with a valid certificate and restrict inbound access
to your own network or identity-aware proxy. Register exactly this HTTPS callback
path as the Kite app redirect URL:

```text
https://your-gateway-domain.example/v1/kite/callback
```

On that server, install the optional runtime and create a server-only environment
file from [kite-execution-gateway.env.example](../../deploy/kite-execution-gateway.env.example):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install ".[execution_gateway]"
gunicorn --workers 1 --bind 127.0.0.1:8080 quantlab.kite_execution_gateway.wsgi:application
```

Use exactly one worker: the access token is deliberately memory-only, so multiple
workers would not share a session. Your reverse proxy terminates TLS and forwards
only to `127.0.0.1:8080`. Do not publish the Gunicorn port directly.

Generate two independent random values on the server: one bearer token for this
specific desktop and one Base32 secret imported into your authenticator app. Never
put either in Git, logs, screenshots, or chat.

Before enabling orders, determine your hashed Kite account identity using the
read-only observer, set a very small explicit symbol allowlist and notional ceiling,
then verify login, preview, rejection, TOTP, and timeout behaviour with
`KITE_EXECUTION_ENABLED=false`. Only after that deliberate operational validation
may you set `KITE_EXECUTION_ENABLED=true` on the gateway server and restart it.

## Configure the desktop

The desktop `.env` receives only these values:

```dotenv
KITE_EXECUTION_GATEWAY_URL=https://your-gateway-domain.example
KITE_EXECUTION_GATEWAY_CLIENT_TOKEN=the-limited-desktop-token
```

Restart QUANT LAB, open **Manual Execution Console**, use **Open Kite login**, then
capture a fresh read-only Broker Gateway snapshot. Preview the order, independently
review the exact hash and notional, type the full confirmation phrase and the current
authenticator code, and accept the final native confirmation dialog.

`KITE_EXECUTION_ENABLED` is false by default. It is a server-only switch; setting
desktop environment flags cannot enable the remote gateway.
