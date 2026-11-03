# NexaHome

Version 0.1 · Last reviewed 2026-11-03

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

- Built: repository, documentation, local checks, a pre-commit hook, a stack template, and seven stacks (`hello`, `actual`, `backup`, `edge`, `identity`, `portal`, `gatus`) on a Colima runtime.
- Package: `src/nexahome`, the `nexahome` command (`doctor`, `check`, `env`, `init`, `config`, `stacks`, `status`, `update`) with tests, built on the `feat/packaging` branch and not yet released ([ADR 0018](adr/0018-code-package-and-language-strategy.md), drafted); the pre-commit hook and `make check` run its checks, and the wheel carries the stacks; `nexahome init` makes a folder of them for someone who does not clone (no release yet); `make` remains the way to start and stop stacks in a clone.
- Published: public repository, secret scanning and push protection on, `main` protected (pull requests only).
- CI: runs on every push and pull request to `main` and `dev`; first successful run on 2026-10-20 (see the [session log](session-log.md), which holds the latest status and pending items).

## Decision register

Status values: **Confirmed** (explicitly agreed), **Proposed** (suggested, not yet agreed), **Open** (undecided). A status changes only with the owner's explicit agreement.

| Decision | Status | Rationale | ADR |
| :--- | :--- | :--- | :--- |
| **Process** | | | |
| Docker Compose is the container orchestrator | Confirmed | Simplest workable option | [0001](adr/0001-docker-compose.md) |
| Branching: `main` ← `dev` ← `feat/<topic>`; merges into `main` only by pull request | Confirmed | Stable main, isolated work | [0002](adr/0002-branching.md) |
| Required CI status checks on `main`: `secrets` and `checks` | Confirmed | CI passes; a failing check must block merges | n/a |
| Foundation first: repository, docs, guardrails, secret scanning, one trivial service | Confirmed | Smallest useful first deliverable | n/a |
| Commit identity: GitHub handle with noreply address, repository-local | Confirmed | Nothing personal in public history | n/a |
| Documentation conventions and one-owner-per-fact rule ([docs/README.md](README.md)) | Proposed | Keeps the set consistent as it grows | n/a |
| Two entry points (README to use, CONTRIBUTING to develop) and an upstream/instance boundary | Confirmed | Each reader sees only what they need; owner data stays untracked | [0006](adr/0006-concerns-and-audiences.md) |
| Stack contract: `_template`, volume label `nexahome.backup`, project name `nexahome-<directory>`, `CHANGE_ME` placeholders | Confirmed | Backups and tooling treat every stack the same | [0007](adr/0007-stack-contract.md) |
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
| Dependabot for pinned image tags, Action SHAs and dev tools | Confirmed | Pins rot without updates | n/a |
| Backup tool: restic in a one-shot container | Confirmed | Restore drill passed 2026-10-21; decision delegated by the owner | [0008](adr/0008-backup-tool.md) |
| First application: Actual Budget (`stacks/actual`) | Confirmed | Real SQLite data for the restore drill; drill subject only, an own expense app is planned for P8 | [0009](adr/0009-first-app-actual-budget.md) |
| **Users and availability** | | | |
| One owner and administrator; hosting for others is a non-goal | Confirmed | Keeps trust and identity simple | n/a |
| Best-effort availability, no service level | Confirmed | Hobby scale | n/a |
| Audience: blueprint to read and fork; pull requests welcome; no support promise | Confirmed | Honest expectations | n/a |
| The owner is the sole administrator; roles `admin` and `users`, an AI agent is never admin; one small shared identity provider (OIDC) is planned in P2.5 | Proposed | The planned apps and roles meet the old trigger; built small ([roadmap](roadmap.md#p25-identity-edge-and-portal)) | n/a |
| Identity provider: Pocket ID in `stacks/identity`; its My Apps page is the one sign-in page; status board stays open on loopback; agents have no account yet ([ADR 0010](adr/0010-identity-provider.md)) | Confirmed | Owner's yes on 2026-11-02 (decision batch, item 1; sub-items marked Proposed in the ADR stay open). Smallest design meeting the owner's roles and agent rule; no extra service | n/a |
| Edge: Caddy in `stacks/edge`, local names under `NEXAHOME_DOMAIN`, shared network `nexahome-edge` ([ADR 0011](adr/0011-edge-and-local-hostnames.md)) | Confirmed | Owner's yes on 2026-11-02 (decision batch, item 2). OIDC needs one issuer name for browser and containers | n/a |
| Portal: Homepage in `stacks/portal`, an open read-only status board at `home.<domain>`, no Docker socket, tiles as YAML in Git, health dots through the edge ([ADR 0012](adr/0012-portal.md)) | Confirmed | Owner's yes on 2026-11-02 (decision batch, item 3). Smallest board that meets the launchpad need without a socket or its own users | n/a |
| Phase P3 (health view) goes ahead as the next phase | Confirmed | Owner's yes on 2026-10-26 ("P3 confirmed"); the tool choice below stays Proposed | n/a |
| Health view: Gatus in `stacks/gatus` (YAML targets in Git, checks through the edge, no Docker socket), with a six-line local Dockerfile; logs stay with `docker compose logs`; no real notification channel and no backup tile yet ([ADR 0013](adr/0013-health-view.md)) | Confirmed | Owner's yes on 2026-10-26 ("I accept ADR 0013"). Smallest tool meeting history and alerts: 5 to 7 MiB, config as code; Uptime Kuma needs a UI database and a claimable setup page | n/a |
| **Hardware** | | | |
| Hardware order: Mac mini, then NAS and UPS, then network upgrades | Confirmed | Owner's plan | n/a |
| Timing of each hardware step | Open | No dates yet | n/a |
| SSH from the MacBook Air to the Mac mini (goal) | Confirmed | Remote administration, deployment, backups | n/a |
| SSH method: keys only, LAN only, no VPN until a need exists ([ADR 0015](adr/0015-remote-access.md), [runbook](runbooks/mini-ssh.md)) | Proposed | Drafted and rehearsed on the laptop in P4 A1; unconfirmed until the mini exists (B1) | n/a |
| VPN choice (Tailscale or WireGuard) | Open | Leans WireGuard; trigger is the first need from outside the home; built in P6 | n/a |
| Mac mini configuration: M6, 32 GB, 512 GB, plus a small external SSD ([ADR 0014](adr/0014-mac-mini-hardware.md)) | Proposed | Ordered by the owner; confirmed or corrected in B2 inside the return window | n/a |
| Sleep, power, FileVault and update policy for the mini ([ADR 0016](adr/0016-mac-mini-power-and-updates.md)) | Proposed | No automatic sleep (manual sleep allowed), restart after power failure, FileVault on, manual updates; drafted in P4 A2, unconfirmed until B1 and B2 | n/a |
| Deploy flow to the mini: `make deploy` in a deploy-only checkout (pull over anonymous HTTPS, check, up), stacks listed per host in `.config/stacks` ([ADR 0017](adr/0017-deploy-flow.md)) | Proposed | Drafted and rehearsed on the laptop in P4 A3; unconfirmed until B2. Open inside it: `make smoke` on a host without the edge | n/a |
| **Packaging** | | | |
| Code package and language strategy: `sh` glue, Python 3.13 or newer with the standard library only, staged (doctor, init, upgrade, run-path ports after B2) ([ADR 0018](adr/0018-code-package-and-language-strategy.md)) | Proposed | Tested logic and one install path; amends by reference the no-`pyproject.toml` row and ADR 0007, neither edited | [0018](adr/0018-code-package-and-language-strategy.md) |
| Platform support and CI matrix: macOS and Linux, WSL2 as Linux best effort, Ubuntu amd64 and arm64 plus macOS arm64 jobs, optional `gate` job ([ADR 0019](adr/0019-platform-support-and-ci-matrix.md)) | Proposed | Turns portability from a claim into evidence; would reword the "Windows is not a target" scope line | [0019](adr/0019-platform-support-and-ci-matrix.md) |
| Instance, install and release model: `nexahome init`, package-owned stacks plus Compose overrides, GitHub release wheel with checksums, first tag `v0.1.0` ([ADR 0020](adr/0020-instance-install-and-release-model.md)) | Proposed | A five-minute path for runners; forks stay the route for customisers | [0020](adr/0020-instance-install-and-release-model.md) |
| Command-line performance: pay for what you use (fast start-up, memory near the bare interpreter, work only when asked; enforced by tests) ([ADR 0021](adr/0021-command-line-performance.md)) | Confirmed | The owner's design principle for Python tools; `--version` 46.7 ms to 15.3 ms, `stacks` 303 ms to 112 ms | [0021](adr/0021-command-line-performance.md) |

## Open questions

Not decided and not blocking: capability priority order; local AI model size (the laptop has 8 GB, so only a small model runs there; the laptop test was dropped and the mini is sized in ADR 0014); home automation scope (no devices yet); storage volume, budget and power limits; macOS version; optional SSH-signed commits; a trademark check on the name (a basic web search found no clash, not a trademark search).

Changelog: 0.1 (2026-11-03): current status names `init` and `config` (PK6, Current status only); 0.1 (2026-11-03): current status says the hook and `make check` use the package and the wheel carries the stacks (PK5, Current status only); 0.1 (2026-11-02): current status names the command `env`, not `setup` (CI redesign session, Current status only); 0.1 (2026-11-02): command-line performance row (ADR 0021) Proposed to Confirmed, owner's yes; 0.1 (2026-11-02): Proposed row for the command-line performance principle, ADR 0021 (PK4); 0.1 (2026-11-02): current status mentions the nexahome package (PK4, Current status only); 0.1 (2026-11-02): ADR 0012 portal row Proposed to Confirmed, owner's yes (F9 item 3); 0.1 (2026-11-02): ADR 0011 edge row Proposed to Confirmed, owner's yes (F9 item 2); 0.1 (2026-11-02): ADR 0010 identity row Proposed to Confirmed, owner's yes (F9 item 1); 0.1 (2026-11-02): open question on the laptop model test updated (PK2); 0.1 (2026-11-02): current status updated to seven stacks and regular CI (PK2); 0.1 (2026-11-02): ADRs 0018 to 0020 written, three Packaging rows added as Proposed; 0.1 (2026-11-02): ADR 0017 written, deploy flow row Open to Proposed; 0.1 (2026-11-02): ADR 0016 written, power policy row Open to Proposed; 0.1 (2026-11-02): ADRs 0014 and 0015 written (Proposed), SSH method and VPN split into two rows; 0.1 (2026-10-26): P4 planned, four hardware rows added (Open), open-questions wording; 0.1 (2026-10-26): P3 session 3 done (ntfy notifier opt-in, Health widget removed, results in ADR 0013); 0.1 (2026-10-26): ADR 0013 and the health tool row Confirmed (owner's yes); 0.1 (2026-10-26): P3 confirmed row, health tool row (Proposed); 0.1 (2026-10-22): identity provider and edge rows (Proposed); 0.1 (2026-10-21): ADRs 0006 and 0009 Confirmed (owner delegated); 0.1 (2026-10-21): ADRs 0007 and 0008 Confirmed (owner delegated), identity row reworded (Proposed); version renamed from 1.0; 0.1 (2026-10-21): first-app row reworded (drill subject only); 0.1 (2026-10-21): stack contract and first-app rows (Proposed), status line; 0.1 (2026-10-21): entry-points row added (Proposed); 0.1 (2026-10-20): Dependabot confirmed; planned services list and open-source rule added; restructured; metadata and working-method sections removed; decisions regrouped; frugality, users, audience and hardware-order rows added.
