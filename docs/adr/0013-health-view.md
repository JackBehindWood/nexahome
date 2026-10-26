# 0013. Health view: Gatus

* **Status:** Proposed
* **Date:** 2026-10-26

## Context
P3 wants history and notifications on top of the portal's red/green dots ([ADR 0012](0012-portal.md)), without a Docker socket and without a new login. Two shortlist tools were measured in throwaway Compose projects on 2026-10-26 (macOS, Colima 2 CPU / 2 GB, arm64), both removed afterwards. Homepage is already the portal; Beszel needs an agent with host or socket access.

Requirements and how each is verified: HV1 up/down per stack, red within about two intervals (browser cards, tool API vs `make smoke`); HV2 history survives a restart (restart test); HV3 a notification mechanism proven on a local webhook, no real channel wired; HV4 RAM limit about 4x idle within R6 (`docker stats`); HV5 non-root, read-only root filesystem, `cap_drop: ALL`, no socket, no published port, working Compose health check (`make check`, `make smoke`, `docker inspect`); HV6 no outbound except a configured notifier, first run not claimable by a page in the browser (socket probe, first-run test); HV7 stopping it breaks nothing (`make smoke`, cards); HV8 targets in a Git file, hostnames only from `NEXAHOME_DOMAIN` and `EDGE_PORT`, fresh clone rebuilds without clicks; HV9 arm64, exact tag, open licence. Logs are out of scope.

## Decision (Proposed)
`stacks/gatus`: Gatus `ghcr.io/twin/gatus:v5.37.0` (Apache-2.0, Go, one binary), targets in `config/config.yaml`, checks through the edge aliases (the same URLs as the portal tiles) plus the edge's `/health`, alert section present but empty. A six-line local `Dockerfile` (no new dependency) builds on the pinned image and adds a static busybox (`busybox:1.37.0-musl`, for the `wget` health check) and a `/data` directory owned by uid 1001, because the upstream image is `scratch`: no shell, no `wget`, and a fresh volume is root-owned. History in SQLite in a named volume labelled `nexahome.backup: "false"` (disposable: config is in Git; owner may choose `"true"`). The owner accepted writing small local code where a gap needs it.

| Item | Gatus v5.37.0 | Uptime Kuma 2.5.6 |
| :-- | :-- | :-- |
| Image | arm64; 72.9 MB on disk; runs as user 1001 with the Dockerfile | arm64; 2.5 GB on disk (603 MB image size); runs as uid 1000 (`node`); `/app/data` owned by `node`, so 1001 fails with `EACCES` |
| Idle RAM | 5 to 6.5 MiB (`docker stats`, with SQLite and 5 targets at 30 s) | 105 to 107 MiB (at the setup page, no monitors) |
| Config | YAML in Git; `${NEXAHOME_DOMAIN}` and `${EDGE_PORT}` substitution works | UI only, stored in its database (fails HV8) |
| Health check | None possible upstream; works with the busybox layer (healthy) | Built in (`extra/healthcheck`), healthy |
| Hardening | `read_only`, `cap_drop: ALL`, `no-new-privileges`: works | same flags started with `tmpfs /tmp`; not tested further (stopped early) |
| First run | No accounts, UI is read-only | `/setup-database` open to the first visitor; a page in the browser can reach it through `*.localhost` (fails HV6) |
| Outbound | Only the five edge connections (private), seen from the shared network namespace | not measured (stopped early) |
| Alerts | Custom webhook triggered and resolved with failure-threshold 2, as the Gatus log shows | not tested |
| Licence | Apache-2.0 | MIT |

Failure modes, shown: **tool down** (container stopped): `make smoke` still passes, portal and stacks unaffected. **Target down** (`make down STACK=actual`): red at the first check after the stop (within 30 s), alert after the second, resolved alert about 30 s after `make up`. **Data lost** (volume deleted): history gone, config and targets returned from Git, tool healthy again in under a minute. Restart: 30 results before, all kept after.

## Consequences
Easier: one YAML file in Git is the whole configuration, 5 to 7 MiB leaves the R6 budget almost untouched. Harder: a local build (`docker compose up --build`) and a Dockerfile Dependabot must follow; targets are a second list next to the portal tiles, so `make smoke` gains the target list in its contract check. The portal tile keeps its own dot. Not decided here: a real notification channel (a sleeping laptop cannot alert; remote channels leave the machine) and the backup-freshness tile (needs a heartbeat from `make backup`, a change to ADR 0008; revisit with the first always-on host). Logs stay with `docker compose logs`: without the socket no tool can show them.
Evolution: laptop (now), then Mac mini (may sleep, so not the monitor's home), then an always-on Linux host or NAS: the monitor, a heartbeat for the backup and a real notifier move there; the YAML, the Dockerfile and the alias names stay. Honest limit: on the laptop the monitor shares its failure domain with what it watches, so it proves the tool, not the health of an always-on system. Auth for the tool UI waits for the leaving-loopback gate ([ADR 0011](0011-edge-and-local-hostnames.md)).
Not verified: Chrome, Firefox, Linux, a real notifier, laptop sleep and clock drift, long-run disk growth, an upgrade between tags, the UI scenarios (owner cards in session 2), alert body capture (the listener saw the request, not the body), Kuma beyond the setup page.

## Alternatives
Uptime Kuma: rejected on HV6 and HV8 and on size; its built-in health check and notifier list are better. Homepage only: no history. Beszel, Prometheus with Grafana and Loki, Netdata: socket or host access, or several services on a 2 GB VM. A monitor of our own: no gain over a 24 MB tool.
