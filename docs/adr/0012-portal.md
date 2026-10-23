# 0012. Portal: Homepage as an open status board

* **Status:** Proposed
* **Date:** 2026-10-23

## Context
P2.5 needs one place to see which stacks run and to open them, without a Docker socket, accounts or code of our own. Measured in session 4 (macOS, Colima 2 CPU / 2 GB, Safari). Requirements: PR1 open, read-only, no secrets (`make smoke`); PR2 one tile and dot per UI stack (T1, T2); PR3 portal down breaks nothing (T3); PR4 non-root, read-only, no socket, no published port (`make check`, smoke); PR5 no outbound connections (smoke); PR6 within R6 (`docker stats`); PR7 hostnames only from `NEXAHOME_DOMAIN` and `EDGE_PORT`; PR8 a new app joins in four steps (R10 dry run); PR9 foreign Host gets the edge's 404.

## Decision
`stacks/portal`: Homepage `ghcr.io/gethomepage/homepage:v2.6.0` (GPL-3.0, run unmodified; config is data), reached only at `home.<domain>:<port>` through the edge (the one alias not named after its stack; `make open STACK=portal` maps it). Open on loopback; gating moves to the leaving-loopback gate in [ADR 0011](0011-edge-and-local-hostnames.md); sign-in stays Pocket ID's My Apps ([ADR 0010](0010-identity-provider.md)). Interface: an edge alias, a Caddyfile block and one entry in `config/services.yaml` (`href`, `siteMonitor` via the alias with `{{HOMEPAGE_VAR_DOMAIN}}` and `{{HOMEPAGE_VAR_PORT}}`). The tile list in Git is the only source of tiles; `make smoke` reports alias, block and tile drift on the running system, `make check` does not (deferred to the first miss).
Measured: 96 MiB anonymous (104 in `docker stats`; limit 256m, R6 met), image 369 MB, no outbound connections, no socket, no published port, config mounted read-only with tmpfs for logs and cache (needs the `config/logs` mount point and every skeleton file), templating works in `href` and `siteMonitor`, config edits apply without restart, status API `/api/siteMonitor`.
Failure modes (verified): portal down: no tiles, all else works; edge down: names and portal dead, apps on loopback ports work; identity down: its dot red, Actual green; portal before edge: red dots, green unaided when the edge is up. R10 dry run: `hello` added in about 30 s; four checklist errors fixed.

## Consequences
Evolution: only the host moves per hardware hop; Compose files and YAML stay. History and alerts go to P3 (the portal links it). `make audit`, `make login-link` and `make env-set` wait for the next OIDC client. Not verified: Chrome, Firefox, Linux, the browser refresh interval. Dropped for size: a published portal port (the edge is the only way in).

## Alternatives
Homarr (socket, own users), Dashy (YAML-heavy), Homepage with Docker discovery (needs the socket), gating the portal now (extra proxy; kept for the leaving-loopback gate), no portal (no health dots).
