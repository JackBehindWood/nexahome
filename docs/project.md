# NexaHome

Version 0.1 · Last reviewed 2026-11-04

A modular, self-hosted homelab platform: local AI, development tools, storage, networking, home automation and personal applications.

## Vision

- **Modular:** components can be added, removed, replaced or migrated without disturbing the rest.
- **Reproducible:** the system can be rebuilt from the repository and a backup.
- **Frugal:** affordable, energy efficient and low maintenance; minimal compute, power and storage; open source first, no paid subscriptions; complexity only when justified (see [constraints](constraints.md#principles)).
- **Portable:** runs unchanged on macOS and Linux; platform-specific parts are isolated and explained.
- **Incremental:** start on a laptop, grow onto dedicated hardware with documented migration steps ([architecture](architecture.md#migration-paths)).

## Scope and non-goals

In scope, built incrementally, starting with what is useful today and delivered as Compose stacks plus the documents and checks that keep them safe. Hosts and phases are in the [architecture](architecture.md#capabilities-hosts-and-phases) table.

- **Development:** Git, VS Code Remote-SSH, Claude Code, automated builds and tests.
- **Local AI:** local models, coding agents, later a modular personal assistant.
- **Storage and backups:** file storage, photo management, reliable backups.
- **Personal applications:** expense tracking, stock and portfolio tracking.
- **Home automation:** Home Assistant, MQTT, ESP32 projects.
- **Networking and security:** VPN, internal DNS, ad blocking, secure remote access.
- **Media:** self-hosted streaming.
- **Management:** service dashboard, health monitoring, logs, notifications.

Not in scope: Kubernetes or custom orchestration, public exposure of administrative interfaces, hosting for other people. Windows is not a target.

## Audience and users

- **Reader:** a blueprint to read, fork, or run as shipped on your own host with your own data. One owner, no hosting for others; pull requests are welcome; there is no support promise.
- **User:** one owner and administrator. A household is considered unlikely; an admin account model is described in [architecture](architecture.md#secrets-and-identity).
- **Availability:** best effort, no service level. A manual recovery path is enough.

## Current status

- Built: repository, documentation, local checks, a pre-commit hook, a stack template, and seven stacks (`hello`, `actual`, `backup`, `edge`, `identity`, `portal`, `gatus`) on a Colima runtime.
- Package: `src/nexahome`, the `nexahome` command (its commands are in the [README](../README.md#the-nexahome-command)) with tests, merged into `main`, not yet released ([ADR 0018](adr/0018-code-package-and-language-strategy.md), drafted); the pre-commit hook and `make check` run its checks, and the wheel carries the stacks; `nexahome init` makes a folder of them for someone who does not clone (no release yet); `make` remains the way to start and stop stacks in a clone.
- Published: public repository, secret scanning and push protection on, `main` protected (pull requests only).
- CI: runs on every push and pull request to `main` and `dev`; the latest result and pending items are in the [session log](session-log.md).

## Decision register

Status values: **Confirmed** (explicitly agreed), **Proposed** (suggested, not yet agreed), **Open** (undecided). A status changes only with the owner's explicit agreement.

| Decision | Status | Rationale | ADR |
| :--- | :--- | :--- | :--- |
| **Process** | | | |
| Docker Compose is the container orchestrator | Confirmed | Simplest workable option | [0001](adr/0001-docker-compose.md) |
| Branching: `main` ← `dev` ← `feat/<topic>`; merges into `main` only by pull request | Confirmed | Stable main, isolated work | [0002](adr/0002-branching.md) |
| Required CI status checks on `main`: `secrets`, `checks` and `gate` | Confirmed | CI passes; a failing check must block merges | n/a |
| Foundation first: repository, docs, guardrails, secret scanning, one trivial service | Confirmed | Smallest useful first deliverable | n/a |
| Commit identity: GitHub handle with noreply address, repository-local | Confirmed | Nothing personal in public history | n/a |
| Documentation conventions and one-owner-per-fact rule ([docs/README.md](README.md)) | Proposed | Keeps the set consistent as it grows | n/a |
| Two entry points (README to use, CONTRIBUTING to develop) and an upstream/instance boundary | Confirmed | Each reader sees only what they need; owner data stays untracked | [0006](adr/0006-concerns-and-audiences.md) |
| Stack contract: `_template`, volume label `nexahome.backup`, project name `nexahome-<directory>`, `CHANGE_ME` placeholders | Confirmed | Backups and tooling treat every stack the same | [0007](adr/0007-stack-contract.md) |
| **Platform** | | | |
| Supported platforms: macOS and Linux | Confirmed | Portability to planned Linux hardware | n/a |
| Container runtime on the laptop: Colima | Confirmed | Light, open source, same docker CLI | [0004](adr/0004-colima-runtime.md) |
| Repository layout: `docs/`, `stacks/`, `src/nexahome/`, `tests/`, `scripts/`, `.github/` and `pyproject.toml`; data outside the tree | Proposed | Separates code, config, secrets and data | n/a |
| Task runner: Makefile for the run path; the `nexahome` command sits beside it ([ADR 0018](adr/0018-code-package-and-language-strategy.md)) | Proposed | No install needed on macOS or Linux | n/a |
| **Security** | | | |
| MIT licence; public repository from the first push | Confirmed | Maximum reuse | n/a |
| Agent configuration (`CLAUDE.md`, `.claude/`) and `.vscode/` are never committed | Confirmed | Private preferences; public docs stay self-contained | [0005](adr/0005-agent-config-local.md) |
| Public-repository security baseline (scanning, hooks, agent permissions) | Proposed | A public repository must not leak secrets or personal data | n/a |
| Claude Code sandbox on or off | Open | Safety against friction; currently off | n/a |
| **Tooling** | | | |
| Project-local tooling (`.venv`, pinned dependencies); no global installs; opt-in git hooks | Confirmed | Clean machine, reproducible setup | [0003](adr/0003-project-local-tooling.md) |
| Python tooling: `.venv` via uv if installed, pip otherwise; `pyproject.toml` exists now for the `nexahome` package ([ADR 0018](adr/0018-code-package-and-language-strategy.md), Proposed) | Confirmed | uv is preferred but optional | n/a |
| Frugality: low cost, minimal compute, power and storage; complexity only when justified | Confirmed | Home hardware, small budget | n/a |
| Open-source software first; no paid subscriptions; no always-on workload unless needed | Confirmed | Part of the same frugality aim, stated more precisely | n/a |
| Dependabot for pinned image tags, Action SHAs and dev tools | Confirmed | Pins rot without updates | n/a |
| Backup tool: restic in a one-shot container | Confirmed | Restore drill passed 2026-10-21; decision delegated by the owner | [0008](adr/0008-backup-tool.md) |
| First application: Actual Budget (`stacks/actual`) | Confirmed | Real SQLite data for the restore drill; permanent reference OIDC client and drill subject; an own expense app is planned for P8 | [0009](adr/0009-first-app-actual-budget.md) |
| **Users and availability** | | | |
| One owner and administrator; hosting for others is a non-goal | Confirmed | Keeps trust and identity simple | n/a |
| Best-effort availability, no service level | Confirmed | Hobby scale | n/a |
| Audience: blueprint to read, fork, or run as shipped on your own host with your own data; one owner, no hosting for others; pull requests welcome; no support promise | Confirmed | Honest expectations | n/a |
| The owner is the sole administrator; roles `admin` and `users`, an AI agent is never admin; one small shared identity provider (OIDC) is planned in P2.5 | Proposed | The planned apps and roles meet the old trigger; built small ([roadmap](roadmap.md#p25-identity-edge-and-portal)) | n/a |
| Identity provider: Pocket ID in `stacks/identity`; its My Apps page is the one sign-in page; status board stays open on loopback; agents have no account yet ([ADR 0010](adr/0010-identity-provider.md)) | Confirmed | Owner's yes on 2026-11-02 (decision batch, item 1; sub-items marked Proposed in the ADR stay open). Smallest design meeting the owner's roles and agent rule; no extra service | n/a |
| Edge: Caddy in `stacks/edge`, local names under `NEXAHOME_DOMAIN`, shared network `nexahome-edge` ([ADR 0011](adr/0011-edge-and-local-hostnames.md)) | Confirmed | Owner's yes on 2026-11-02 (decision batch, item 2). OIDC needs one issuer name for browser and containers | n/a |
| Portal: Homepage in `stacks/portal`, an open read-only status board at `home.<domain>`, no Docker socket, tiles as YAML in Git, health dots through the edge ([ADR 0012](adr/0012-portal.md)) | Confirmed | Owner's yes on 2026-11-02 (decision batch, item 3). Smallest board that meets the launchpad need without a socket or its own users | n/a |
| Phase P3 (health view) goes ahead as the next phase | Confirmed | Owner's yes on 2026-10-26 ("P3 confirmed") | n/a |
| Health view: Gatus in `stacks/gatus` (YAML targets in Git, checks through the edge, no Docker socket), with a six-line local Dockerfile; logs stay with `docker compose logs`; ntfy notifier opt-in, off by default; no backup tile yet ([ADR 0013](adr/0013-health-view.md)) | Confirmed | Owner's yes on 2026-10-26 ("I accept ADR 0013"). Smallest tool meeting history and alerts: 5 to 7 MiB, config as code; Uptime Kuma needs a UI database and a claimable setup page | n/a |
| **Hardware** | | | |
| Hardware order: Mac mini, then NAS and UPS, then network upgrades | Confirmed | Owner's plan | n/a |
| Timing of each hardware step | Open | No dates yet | n/a |
| SSH from the MacBook Air to the Mac mini (goal) | Confirmed | Remote administration, deployment, backups | n/a |
| SSH method: keys only, LAN only, no VPN until a need exists ([ADR 0015](adr/0015-remote-access.md), [runbook](runbooks/mini-ssh.md)) | Proposed | Drafted and rehearsed on the laptop in P4 A1; unconfirmed until the mini exists (B1) | n/a |
| VPN choice (Tailscale or WireGuard) | Open | Leans WireGuard; trigger is the first need from outside the home; built in P6 | n/a |
| Mac mini configuration: M6, 32 GB, 512 GB, plus a small external SSD ([ADR 0014](adr/0014-mac-mini-hardware.md)) | Proposed | Planned; confirmed or corrected in B2 inside the vendor's return window | n/a |
| Sleep, power, FileVault and update policy for the mini ([ADR 0016](adr/0016-mac-mini-power-and-updates.md)) | Proposed | No automatic sleep (manual sleep allowed), restart after power failure, FileVault on, manual updates; drafted in P4 A2, unconfirmed until B1 and B2 | n/a |
| Deploy flow to the mini: `make deploy` in a deploy-only checkout (pull over anonymous HTTPS, check, up), stacks listed per host in `.config/stacks` ([ADR 0017](adr/0017-deploy-flow.md)) | Proposed | Drafted and rehearsed on the laptop in P4 A3; unconfirmed until B2. Open inside it: `make smoke` on a host without the edge | n/a |
| **Packaging** | | | |
| Code package and language strategy: `sh` glue, Python 3.13 or newer with the standard library only, staged (doctor, init, upgrade, run-path ports after B2) ([ADR 0018](adr/0018-code-package-and-language-strategy.md)) | Proposed | Tested logic and one install path; amends the earlier no-`pyproject.toml` wording and ADR 0007, both since updated to match | [0018](adr/0018-code-package-and-language-strategy.md) |
| Platform support and CI matrix: macOS and Linux, WSL2 as Linux best effort, Ubuntu amd64 and arm64 plus macOS arm64 jobs, required `gate` job ([ADR 0019](adr/0019-platform-support-and-ci-matrix.md)) | Proposed | Turns portability from a claim into evidence; would reword the "Windows is not a target" scope line | [0019](adr/0019-platform-support-and-ci-matrix.md) |
| Instance, install and release model: `nexahome init`, package-owned stacks plus Compose overrides, GitHub release wheel with checksums, first tag `v0.2.0` ([ADR 0020](adr/0020-instance-install-and-release-model.md)) | Proposed | A five-minute path for runners; forks stay the route for customisers | [0020](adr/0020-instance-install-and-release-model.md) |
| Command-line performance: pay for what you use (fast start-up, memory near the bare interpreter, work only when asked; enforced by tests) ([ADR 0021](adr/0021-command-line-performance.md)) | Confirmed | The owner's design principle for Python tools; `--version` 46.7 ms to 15.3 ms, `stacks` 303 ms to 112 ms | [0021](adr/0021-command-line-performance.md) |
| Own images and application stacks: adopt before build, a stack contract that needs no language, one template per runtime profile, Python first ([ADR 0022](adr/0022-own-images-and-app-stacks.md)) | Proposed | Owner answers recorded 2026-11-03; nothing built until the first owner-written app; Go only for upstream software | [0022](adr/0022-own-images-and-app-stacks.md) |

## Open questions

Not decided and not blocking: capability priority order; local AI model size (the laptop has 8 GB, so only a small model runs there; the laptop test was dropped and the mini is sized in ADR 0014); home automation scope (no devices yet); storage volume, budget and power limits; macOS version; optional SSH-signed commits; a trademark check on the name (a basic web search found no clash, not a trademark search).

Changelog: 0.1 (2026-11-04): audience row worded for running as shipped (Confirmed row, owner's yes), health-phase row and four Proposed rows reworded, command list and CI date removed from current status (DR3); 0.1 (2026-11-04): Actual Budget row names the permanent reference client (DR2); 0.1 (2026-11-04): register row for ADR 0022, own images and application stacks (Proposed); 0.1 (2026-11-03): Python tooling row notes `pyproject.toml` exists, first tag wording `v0.2.0` (PK6f, owner's yes); 0.1 (2026-11-03): register rows for required checks and the health view corrected, the mini row worded as a plan (PK6c); 0.1 (2026-11-03): the package is merged into `main` (current status, PK6c); 0.1 (2026-11-03): current status names `init` and `config` (PK6, Current status only); 0.1 (2026-11-03): current status says the hook and `make check` use the package and the wheel carries the stacks (PK5, Current status only)
