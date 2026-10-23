# portal

[Homepage](https://gethomepage.dev) as an open, read-only status board: one tile per stack with a web UI and a health dot ([ADR 0012](../../docs/adr/0012-portal.md), Proposed). Reached by name through the edge at `home.<domain>:<port>`; it publishes no port, has no login, no widgets and no Docker socket. Run unmodified (GPL-3.0); the tiles are plain YAML in `config/`.

```sh
make up STACK=portal      # start and wait until healthy
make portal               # starts the edge and the portal, opens http://home.<domain>:<port>/
make smoke                # read-only checks of everything that runs
make down STACK=portal
```

| Item | Value |
| :--- | :--- |
| RAM (measured, idle, 2026-10-23) | 96 MiB anonymous, 104 MiB in `docker stats` (limit 256 MiB) |
| Disk (measured) | image 369 MB; no volume |
| Must run 24/7? | no |
| Backed up | nothing; `config/` is in Git |
| Verify after a restore | `make smoke` prints `ok tile dot ...` for every tile |

Tiles: `config/services.yaml`. Host names use `{{HOMEPAGE_VAR_DOMAIN}}` and `{{HOMEPAGE_VAR_PORT}}`, which the compose file fills from `NEXAHOME_DOMAIN` and `EDGE_PORT` (equal to the edge's `.env`). A new app needs one tile ([add a stack](../../docs/runbooks/add-a-stack.md)). The dot is `siteMonitor` through the edge alias, so a red dot means the named URL does not answer.

Hardening: uid 1001, read-only root, `config/` mounted read-only, tmpfs for logs and the build cache, all capabilities dropped. Homepage insists on every skeleton file in `config/`; the empty ones and `logs/.gitkeep` (the mount point for the log tmpfs) must stay. Update check, version display and telemetry are off; no remote assets. Dummy data only.
