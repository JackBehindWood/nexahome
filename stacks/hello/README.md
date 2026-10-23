# hello

Smallest possible stack: a static page served by BusyBox `httpd`. It exists to prove the pipeline (Compose, health check, localhost-only binding, hardening defaults) and holds no data or secrets.

```sh
make up STACK=hello     # start and wait until healthy
curl http://127.0.0.1:8080/
make down STACK=hello
```

Port is configurable with `HELLO_PORT` (see `.env.example`).

On the edge since the R10 dry run: `http://hello.<domain>:<port>/` (alias on the edge, one Caddyfile block, one portal tile); `make smoke` checks all three.
