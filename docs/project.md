# NexaHome

Version 1.0 · Last reviewed 2026-10-20

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

- **Reader:** a blueprint to read and fork. Pull requests are welcome; there is no support promise.
- **User:** one owner and administrator. A household is considered unlikely; an admin account model is described in [architecture](architecture.md#secrets-and-identity).
- **Availability:** best effort, no service level. A manual recovery path is enough.

## Current status

- Built: repository, documentation, local checks, a pre-commit hook, the `hello` demo stack on a Colima runtime.
- Published: public repository, secret scanning and push protection on, `main` protected (pull requests only).
- CI: first successful run on 2026-10-20 (see the [session log](session-log.md), which holds the latest status and pending items).

## Decision register

Status values: **Confirmed** (explicitly agreed), **Proposed** (suggested, not yet agreed), **Open** (undecided). A status changes only with the owner's explicit agreement.

| Decision | Status | Rationale | ADR |
| :--- | :--- | :--- | :--- |
| **Process** | | | |
| Docker Compose is the container orchestrator | Confirmed | Simplest workable option | [0001](adr/0001-docker-compose.md) |
| Branching: `main` ← `dev` ← `feat/<topic>`; merges into `main` only by pull request | Confirmed | Stable main, isolated work | [0002](adr/0002-branching.md) |
| Required CI status checks on `main` | Open | CI has now passed once; requiring `secrets` and `checks` is recommended, awaiting the owner's yes | n/a |
| Foundation first: repository, docs, guardrails, secret scanning, one trivial service | Confirmed | Smallest useful first deliverable | n/a |
| Commit identity: GitHub handle with noreply address, repository-local | Confirmed | Nothing personal in public history | n/a |
| Documentation conventions and one-owner-per-fact rule ([docs/README.md](README.md)) | Proposed | Keeps the set consistent as it grows | n/a |
| **Platform** | | | |
| Supported platforms: macOS and Linux | Confirmed | Portability to planned Linux hardware | n/a |
| Container runtime on the laptop: Colima | Confirmed | Light, open source, same docker CLI | [0004](adr/0004-colima-runtime.md) |
| Repository layout: `docs/`, `stacks/`, `scripts/`, data outside the tree | Proposed | Separates code, config, secrets and data | n/a |
| Task runner: Makefile | Proposed | No install needed on macOS or Linux | n/a |
| **Security** | | | |
| MIT licence; public repository from the first push | Confirmed | Maximum reuse | n/a |
| Agent configuration (`CLAUDE.md`, `.claude/`) and `.vscode/` are never committed | Confirmed | Private preferences; public docs stay self-contained | [0005](adr/0005-agent-config-local.md) |
| Public-repository security baseline (scanning, hooks, agent permissions) | Proposed | A public repository must not leak secrets or personal data | n/a |
| Claude Code sandbox on or off | Open | Safety against friction; currently off | n/a |
| **Tooling** | | | |
| Project-local tooling (`.venv`, pinned dependencies); no global installs; opt-in git hooks | Confirmed | Clean machine, reproducible setup | [0003](adr/0003-project-local-tooling.md) |
| Python tooling: `.venv` via uv if installed, pip otherwise; no `pyproject.toml` until Python code needs it | Confirmed | uv is preferred but optional | n/a |
| Frugality: low cost, minimal compute, power and storage; complexity only when justified | Confirmed | Home hardware, small budget | n/a |
| Open-source software first; no paid subscriptions; no always-on workload unless needed | Confirmed | Part of the same frugality aim, stated more precisely | n/a |
| Dependabot for pinned image tags and Action SHAs | Proposed | Pins rot without updates | n/a |
| Backup tool (restic is the shortlist) | Open | Chosen when the restore drill is built | n/a |
| **Users and availability** | | | |
| One owner and administrator; hosting for others is a non-goal | Confirmed | Keeps trust and identity simple | n/a |
| Best-effort availability, no service level | Confirmed | Hobby scale | n/a |
| Audience: blueprint to read and fork; pull requests welcome; no support promise | Confirmed | Honest expectations | n/a |
| Single admin account; no SSO or identity provider until a second user or a service needs one | Proposed | Avoids unneeded infrastructure | n/a |
| **Hardware** | | | |
| Hardware order: Mac mini, then NAS and UPS, then network upgrades | Confirmed | Owner's plan | n/a |
| Timing of each hardware step | Open | No dates yet | n/a |
| SSH from the MacBook Air to the Mac mini (goal) | Confirmed | Remote administration, deployment, backups | n/a |
| SSH method and VPN choice (Tailscale or WireGuard) | Open | Hardware-gated | n/a |

## Open questions

Not decided and not blocking: capability priority order; local AI model size (the laptop has 8 GB, so no local model runs there); home automation scope (no devices yet); storage volume, budget and power limits; macOS version; optional SSH-signed commits; a trademark check on the name (a basic web search found no clash, not a trademark search).

Changelog: 1.0 (2026-10-20): planned services list and open-source rule added; restructured; metadata and working-method sections removed; decisions regrouped; frugality, users, audience and hardware-order rows added.
