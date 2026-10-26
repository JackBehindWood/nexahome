# gatus

[Gatus](https://github.com/TwiN/gatus) as the health view: it checks every named URL through the edge like a browser, shows red/green with history, and can notify ([ADR 0013](../../docs/adr/0013-health-view.md), Proposed). Reached by name at `gatus.<domain>:<port>`; it publishes no port, has no login (read-only page) and no Docker socket. Built locally from a six-line `Dockerfile` because the upstream image has no shell for a health check and a fresh volume is root-owned.

```sh
make up STACK=gatus       # build, start and wait until healthy
make open STACK=gatus     # opens http://gatus.<domain>:<port>/
make down STACK=gatus     # stopping it breaks nothing else
```

| Item | Value |
| :--- | :--- |
| RAM (measured, idle, 2026-10-26) | 6.6 MiB in `docker stats` with 5 targets at 30 s (limit 32 MiB) |
| Disk (measured) | image 75 MB; history in SQLite in the volume `data` (growth not measured long-term) |
| Must run 24/7? | no (history has a gap while it is off) |
| Backed up | nothing: volume `data` is labelled `"false"`, targets are in `config/` (Git) |
| Verify after a rebuild | `make smoke` prints `ok gatus healthy` and `ok contract`; all targets green on the page |

**Targets:** `config/config.yaml`, one entry per named URL, hostnames from `NEXAHOME_DOMAIN` and `EDGE_PORT`. A new app needs one entry here and one portal tile ([add a stack](../../docs/runbooks/add-a-stack.md)); `make smoke` lists a tile without a target. After editing run `docker compose restart` in this directory.

**Portal:** the Health tile is a link with its own up/down dot, no widget (a widget shows a DNS error when this stack is down). The dots keep working if this stack is down.

**Alerts:** off by default (`NTFY_TOPIC` empty, nothing leaves the machine). Channel: [ntfy](https://ntfy.sh), free to use without an account (paid plans only raise limits such as messages per day; you can run your own ntfy server and set `NTFY_URL`). A target alerts after 2 failed checks and resolves after 2 passes (`alerting.ntfy.default-alert` in `config/config.yaml`). To turn on:
1. In `stacks/gatus/.env` set `NTFY_URL=https://ntfy.sh` and `NTFY_TOPIC=GENERATE`, then `make up STACK=gatus` (creates a random topic, not printed).
2. Open `.env` yourself to read the topic and subscribe to it in the ntfy app. The topic is the secret: anyone who knows it can read and post.
3. What leaves the machine: the alert title and text (target name, status code, time) to `NTFY_URL`, only when a state changes; ntfy.sh keeps messages about 12 hours. To rotate, change the topic.
Another channel: replace the `alerting:` block with another provider from the [Gatus docs](https://github.com/TwiN/gatus#alerting) and keep `alerts: [{type: <provider>}]` on the endpoints. A sleeping laptop cannot alert.

**Limits:** on this laptop the monitor sleeps with what it watches, so it proves the tool, not an always-on system. The page is read-only without a login and reachable by name from any local web page; it shows service names only. Logs are not shown (no socket): use `docker compose logs`.

Hardening: uid 1001, read-only root, `config/` mounted read-only, all capabilities dropped. Telemetry is not enabled. Remove: `make down STACK=gatus`, delete this directory and its edits; the volume only if you no longer want the history.
