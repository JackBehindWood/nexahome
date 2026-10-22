# 0011. Edge, local hostnames and shared network

* **Status:** Proposed
* **Date:** 2026-10-22 (amended 2026-10-22 after P2.5 session 2; still Proposed)

## Context
OIDC needs an issuer URL that resolves under the same name from the browser and from app containers, so `127.0.0.1` cannot be used ([ADR 0010](0010-identity-provider.md)). The smallest fix is a reverse proxy with local names on a shared network, without public TLS and without ports below 1024. Spike on 2026-10-21 and 2026-10-22 (macOS, Colima 2 CPU / 2 GB, Safari). The measured figures below come from a throwaway Compose project that is removed.

## Decision (Proposed)
- **Edge:** Caddy `caddy:2.11.7-alpine` as `stacks/edge`, stateless. Global `admin off` and `auto_https off`, one `http://<name>.${NEXAHOME_DOMAIN}:${EDGE_PORT}` block per app.
- **Names:** `NEXAHOME_DOMAIN` (default `nexahome.localhost`) is the only source of names. `id.`, `actual.`, `home.` are prefixes.
- **Network:** external network `nexahome-edge`; the edge container carries one alias per hostname, so containers resolve the same names the browser uses. The edge listens on the same port inside the network as the host port it publishes (`127.0.0.1:${EDGE_PORT}:${EDGE_PORT}`), because the issuer contains the port.
- **Portal:** Homepage `ghcr.io/gethomepage/homepage:v2.6.0` as `stacks/portal`, read-only, no Docker socket, health dots through `siteMonitor` on the edge alias.
- **Stack interface (four steps):** join `nexahome-edge` with the alias; one block in the Caddyfile; OIDC client variables and registration; one tile in `services.yaml`.

| Item | Measured |
| :-- | :-- |
| Caddy | arm64; 89 MB; Apache-2.0; no image healthcheck, so a `wget` check on a catch-all `/health`; idle 10 to 15 MiB |
| Caddy hardening | uid 1001, `read_only`, tmpfs `/data` and `/config` with `uid=1001`. `cap_drop: ALL` alone fails (`caddy: Operation not permitted`: the binary carries a file capability). `cap_add: NET_BIND_SERVICE` fixes it, although the port is above 1024: **a flagged deviation from the Compose policy** |
| Homepage | arm64; 369 MB; GPL-3.0 (run unmodified); root by default; ran as uid 1001 with `read_only`, `cap_drop: ALL`, tmpfs for config and caches; built-in healthcheck; idle 106 to 110 MiB. Config as a read-only bind mount with tmpfs for logs: not tested |
| Name resolution | `curl` resolves `*.localhost` to 127.0.0.1; `dscacheutil` does not; Safari loaded the pages (reported). From containers the alias resolved to the edge (`getent`), and Actual (Node) fetched the issuer by it at start. Chrome, Firefox and Linux: not tested |
| Portal check | `siteMonitor` through the alias returned 200, and 502 within 3 s of stopping Actual |
| Outbound / socket | No outside connections or telemetry seen in edge, portal or Actual; nothing mounted from the Docker socket |
| Actual over http | `http://` issuer and `http://*.localhost` redirect URI accepted (stop condition not triggered) |
| R6 | Edge 10 to 15 + identity 17 + portal 106 to 110 = about 133 to 142 MiB, under the 400 MiB budget. With Actual (128 MiB) about 270 MiB; the VM showed 455 MiB used of 1959 MiB with the three new services and the existing Actual stack running (measured before the spike Actual was added) |
| Disk | About 570 MB of new images |
| `make up` core set | Not needed at these figures; revisit if a heavier stack arrives |

## Failure modes
| Down | Effect | Still works |
| :-- | :-- | :-- |
| edge | Hostnames and SSO logins fail | Each app on its own `127.0.0.1` port, existing sessions, password fallback |
| identity | New SSO logins fail | Valid sessions, password fallback |
| portal | No tiles | Everything else |
Unknown hostnames get 404 (built in session 2, verified with a foreign `Host` header). This also limits DNS rebinding against loopback services.

**Built in session 2:** `stacks/edge` and `stacks/identity`, `make up` creates `nexahome-edge` and starts edge and identity first, `check_compose.py` rejects other external networks, `cap_add` other than `NET_BIND_SERVICE` and a Docker socket mount. Measured: edge 10 MiB, identity 16 MiB idle (about 26 MiB, R6 met without the portal), images 89 MB and 110 MB, limits 64 MiB and 128 MiB, log rotation 10 MB x 3, response headers `nosniff`, `no-referrer`, `X-Frame-Options: DENY`. Pocket ID trusts the proxy header (`TRUST_PROXY`); its audit log shows the Docker gateway address, not the browser's.

**Threat model:** loopback services are reachable by local processes and by web pages through DNS rebinding. Controls: the 404 rule, groups on clients, SSO for apps with data. Every stack on `nexahome-edge` can reach every other; per-app networks are the next step when a less trusted stack joins.

## Evolution and migration
| Hop | Changes | Stays |
| :-- | :-- | :-- |
| Laptop to Mac mini | Nothing for these stacks (they stay on the laptop or the future always-on host; the mini may sleep) | Compose files |
| To an always-on host | Edge and identity move together; backup restore of the `identity` volume plus its `.env` | Names, if `NEXAHOME_DOMAIN` is kept |
| Real internal domain (P6) | `NEXAHOME_DOMAIN`, each client's variables; **passkeys must be re-enrolled** (bound to the hostname) | Provider data |
| Linux host | Same files; `*.localhost` resolution to be verified there | |

**Leaving-loopback gate (P6):** before any port binds beyond `127.0.0.1`, gate the portal behind the provider (forward auth), require TLS on the edge, an exposure review, a decision on admin access (VPN only), and a re-test of passkeys and every client on the new names. Not before.

## Alternatives
Traefik or nginx (more config or no gain), `caddy-docker-proxy` and Traefik labels (need the Docker socket), the `caddy-security` plugin (custom build; ties clients to Caddy, breaking R9), forward-auth in front of every app (extra service; kept for apps without OIDC), `/etc/hosts` entries or a local DNS (host changes), Homarr or Dashy (socket mount, own users, YAML-heavy), no edge (breaks OIDC naming).
