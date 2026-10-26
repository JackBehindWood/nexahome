# Observability and operations

Version 0.1 · Last reviewed 2026-10-26

How we see what is running. Today there is one demo stack on one laptop, so the approach is deliberately minimal.

## Decoupling rule

Critical services (DNS, storage, core AI) never depend on monitoring or any dashboard to work. Monitoring may be down without anything else breaking.

## Phase 0: laptop only (current)

No monitoring suite. State comes from:

- Container health checks, required on every service ([Compose policy](constraints.md#compose-policy)).
- `make ps` (or `docker compose ps` in the stack directory): a service is healthy when its status says `healthy`.
- `docker compose logs` for one stack at a time.

Leave phase 0 when a second real service exists or when something broke unnoticed. A real service means one that holds data or that someone uses, not the `hello` demo.

## What we want to see

| Signal | Question it answers | Phase 0 source |
| :--- | :--- | :--- |
| Health | Is each service up and responding? | health checks, `make ps` |
| Logs | Why did it fail? | `docker compose logs` |
| Backups | Did the last backup run and can it be restored? | restore drill ([architecture](architecture.md#data-backup-and-restore)) |
| Deployment state | Which version of which stack is running? | image tags in `compose.yaml`, Git commit |
| Notifications | Who tells me something broke? | None in phase 0. The health tool can send a webhook alert (proven locally); a real channel waits for an always-on host and must not be a paid service |

## Tool shortlist

Chosen (Proposed, [ADR 0013](adr/0013-health-view.md)): Gatus, measured against Uptime Kuma on 2026-10-26. Homepage is the portal ([ADR 0012](adr/0012-portal.md)); Beszel needs host or socket access. Selection criteria were: arm64 image, small memory footprint, runs from Compose, no cloud account, removable without data loss, config in Git, no Docker socket.

## Private inventory

Hostnames and addresses must not be published. Keep the real inventory in a gitignored `inventory.local.md` or outside the repository. Template:

| Field | Example placeholder |
| :--- | :--- |
| Host ID | `host-1` |
| Role | workstation, AI, always-on services, storage |
| Operating system | `<os and version>` |
| Address | `<lan address>` |
| Power | `<UPS or none>` |
| Backup | `<last verified restore date>` |

Changelog: 0.1 (2026-10-26): shortlist result (Gatus, Proposed), notifications row; 0.1 (2026-10-21): version renamed from 1.0 (pre-release project); 0.1 (2026-10-20): notifications signal added; reduced to the decoupling rule, a testable phase 0, a shortlist and an inventory template; dashboard and portal aspirations removed.
