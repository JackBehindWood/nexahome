# edge

[Caddy](https://caddyserver.com) reverse proxy that gives every app a local name (`id.<domain>`, later `actual.<domain>`) on one port, so browsers and containers use the same OIDC issuer URL ([ADR 0011](../../docs/adr/0011-edge-and-local-hostnames.md), Proposed). Stateless; plain http on `127.0.0.1`, no TLS and no admin API. Anything not matched, including a foreign `Host` header, gets 404.

```sh
make up STACK=edge      # creates the shared network nexahome-edge if missing
curl http://127.0.0.1:8088/health
make down STACK=edge
```

| Item | Value |
| :--- | :--- |
| RAM (measured, idle, 2026-10-22) | 10 MiB (limit 64 MiB) |
| Disk (measured) | image 89 MB; no volume |
| Must run 24/7? | no (only while apps are used by name) |
| Backed up | nothing; the Caddyfile is in Git |
| Verify after a restore | `curl -s -o /dev/null -w '%{http_code}' -H 'Host: other.example' http://127.0.0.1:8088/` prints 404 and `/health` prints `ok` |

Add an app: one `aliases` entry in `compose.yaml` and one block in `Caddyfile`, and the app joins the network `nexahome-edge`. `NEXAHOME_DOMAIN` and `EDGE_PORT` must be equal in every stack's `.env`.

Runs as uid 1001, read-only root, tmpfs for `/data` and `/config`. Flagged deviation: `cap_add: NET_BIND_SERVICE` (the binary carries a file capability and does not start with every capability dropped). Everything on `nexahome-edge` can reach everything else on it. Dummy data only.
