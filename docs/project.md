# NexaHome

A modular, self-hosted homelab platform bringing together local AI, development tools, storage, networking, home automation, and personal applications.

---

## Project Metadata

* **Name:** NexaHome
* **Repository Slug:** `nexahome`
* **License / Access:** MIT, public GitHub repository
* **Target Audience:** Self-hosters, home automation enthusiasts, and developers looking for a modular, reproducible homelab blueprint.

---

## 1. Vision & Goals

NexaHome is designed as a small, extensible computing ecosystem. The goal is to build a secure, observable, maintainable, and reproducible system that can evolve over time.

* **Modularity:** Components must be easy to add, remove, replace, or migrate without disrupting the rest of the system.
* **Accessibility:** The project should be documented clearly enough for others to adapt to their own hardware setups, requirements, and budgets.
* **Incremental Evolution:** Start on portable workstation hardware (MacBook Air M3) and grow to dedicated hardware (Mac mini, NAS, homelab servers) with documented migration steps.
* **Platform independence:** Prefer solutions that run unchanged on macOS and Linux. Platform-specific parts are allowed only where unavoidable, isolated, and documented with the reason.

### Non-goals

No Kubernetes or custom orchestration, no public exposure of administrative interfaces, no multi-user hosting. Windows is not a current target (possible later).

---

## 2. Working Method

How the engineering partner (human or AI) works on this project is defined in a local, uncommitted `CLAUDE.md`; the rules that matter to readers are in [`constraints.md`](constraints.md). Significant decisions are recorded as ADRs in [`adr/`](adr/).

---

## 3. Current Status

See [`roadmap.md`](roadmap.md) for the next session and [`session-log.md`](session-log.md) for history. Begin on the **MacBook Air M3** without assuming the Mac mini, NAS, or network upgrades are available, and keep NexaHome useful at every stage.

---

## 4. Decisions

Status: **Confirmed** (explicitly agreed), **Proposed** (suggested, not yet agreed), **Open** (undecided). Statuses change only with the project owner's explicit agreement.

| Decision | Status | Rationale | ADR |
| :--- | :--- | :--- | :--- |
| Docker Compose as the container orchestrator | Confirmed | Simplest workable option; Kubernetes explicitly out | [0001](adr/0001-docker-compose.md) |
| Branching: `main` ← `dev` ← `feat/<topic>`; small commits on `feat/*` | Confirmed | Stable main, integration branch, isolated work | [0002](adr/0002-branching.md) |
| Project-local tooling (`.venv`, pinned deps); no global installs; opt-in git hooks | Confirmed | Keep the machine clean, reproducible setup | [0003](adr/0003-project-local-tooling.md) |
| Agent config (`.claude/`) is never committed; `CLAUDE.md` is also kept local for now | Confirmed (`.claude/`), Proposed (`CLAUDE.md`) | Keeps tooling preferences private; public docs stay self-contained | n/a |
| MIT license; public repository from first push | Confirmed | Maximum reuse; resale by others accepted | n/a |
| Supported platforms: macOS and Linux; prefer platform-independent solutions | Confirmed | Portability to the planned Linux/dedicated hardware | n/a |
| Commit identity: GitHub handle with noreply address, repo-local config | Confirmed | Nothing personal in public history | n/a |
| Foundation first: repo, docs, guardrails, secret scanning, one trivial service | Confirmed | Smallest useful first deliverable | n/a |
| SSH from the MacBook Air to the Mac mini (goal) | Confirmed | Remote administration of the future host | n/a |
| SSH method, VPN choice (Tailscale/WireGuard) | Open | Depends on hardware not yet available | n/a |
| Repository layout (`docs/`, `stacks/`, `scripts/`, data outside the tree) | Proposed | Separates code, config, secrets, data | n/a |
| Public-repo security baseline (scanning, hooks, agent permissions) | Proposed | Public repo must not leak secrets or personal data | n/a |
| Container runtime on the laptop: Colima (open source, light, same docker CLI and Compose files) | Confirmed | Chosen by the owner; lightest option for an Air | [0004](adr/0004-colima-runtime.md) |
| Python tooling: `.venv` via uv if installed, plain pip otherwise; no `pyproject.toml` until Python code needs it | Confirmed | uv is preferred but optional | n/a |
| `.vscode/` is never committed (editor config stays local) | Confirmed | Personal editor preferences stay private | n/a |
| Task runner: Makefile | Proposed | No install needed on macOS/Linux | n/a |
| Claude Code sandbox on or off | Open | Trade-off between safety and friction | n/a |
| Name-collision check for "NexaHome" before first push | Open | Avoid clashing with an existing project | n/a |
