# Roadmap

Version 1.0 · Last reviewed 2026-10-20

What gets built and in what order. Hardware has no dates; phases are ordered by dependency. Update this file at the end of every working session.

## Now, next, later

| When | Work |
| :--- | :--- |
| Now | Prove CI; add Dependabot; merge `dev` into `main` (documentation set 1.0 is merged into `dev`) |
| Next | Persistence and restore drill on the laptop |
| Later | Health view, then the hardware phases in order: Mac mini, NAS and UPS, network, home automation, then personal applications and media |

Pending owner actions are tracked in the [session log](session-log.md), not here.

## Done

- **Session 0, bootstrap:** repository, documents, decisions table, first ADRs, licence, README, SECURITY.
- **Session 1, pipeline proof:** Makefile, project-local tooling, opt-in pre-commit hook, Colima runtime, `hello` stack, Compose policy check, CI workflow file, PR template.
- **Session 2, publish safely (done except the pending items):** history scan, public repository, secret scanning and push protection, `main` protected. Still open: CI has never run; pull request 1 is unmerged.
- **Documentation foundation:** this documentation set, version 1.0.

## Phases

Each phase lists goal, scope, dependencies, hardware gate, exit criteria, verification and definition of done. Done means every exit criterion is verified and the log says so.

### P0 Foundation (done)

Goal: a safe, public, documented starting point. Exit criteria were met by Sessions 0 to 2 except the CI proof, which moved to P1.

### P1 Prove CI and the publishing flow

- **Goal:** a green CI run, and a working merge path. **Depends on:** P0. **Hardware:** none.
- **Scope:** find why no workflow run starts and fix it; add a manual trigger if that is the cause (owner approval for the workflow change); merge pull request 1 into `dev`, then `dev` into `main` by pull request (owner approves each merge); decide whether to require the CI checks on `main`; add `.github/dependabot.yml` for Actions and image tags.
- **Exit criteria:** one successful CI run is linked in the log; `main` and `dev` match; the required-check decision is in the register; Dependabot has opened its first pull request or its config is validated by GitHub.
- **Verification:** `gh run list`, `gh api` on branch protection, `git log`.
- **Sessions:** (1) CI proof; (2) merges; (3) Dependabot.

### P2 Persistence and restore drill

- **Goal:** prove the backup model on the laptop. **Depends on:** P1 (CI proof). **Hardware:** none.
- **Scope:** one real stateful stack (a small database or file service), a backup using the chosen tool (restic is the shortlist, chosen by ADR), a tested restore, a first runbook for restore, a short "add a stack" section.
- **Exit criteria:** data deleted on purpose is restored from backup and checked; the runbook was followed by someone cold; `make check` passes.
- **Verification:** restore drill output recorded in the log. The VM stays at 2 GB, so one extra light stack at a time.
- **Sessions:** (1) stack with a named volume; (2) backup; (3) restore drill and runbook.

### P3 Health view (optional)

- **Goal:** one place to see service health, logs and notifications (the service dashboard). **Depends on:** P2 (a real service to watch). **Hardware:** none.
- **Scope:** compare two tools from the [shortlist](observability.md#tool-shortlist), choose by ADR, deploy as a stack.
- **Exit criteria:** it shows the real stack's state; stopping the tool breaks nothing else (decoupling rule).
- **Sessions:** (1) ADR and deployment.

### P4 Mac mini bootstrap

- **Goal:** the Mac mini is a usable workstation reachable from the laptop. **Depends on:** P1. **Hardware gate:** Mac mini.
- **Scope:** SSH with keys (method decided here; runbook with placeholders), VPN decision (ADR), sleep policy, VS Code Remote-SSH, Claude Code on the mini (local agent files are copied by hand), deploy flow (`git pull`, `make check`, `make up`), backups by file transfer, native local AI sized to the chosen model.
- **Exit criteria:** SSH login works from the laptop; `make check` passes on the mini; a stack starts healthy there; a model answers a prompt natively.
- **Sessions:** (1) SSH and runbook; (2) VPN ADR; (3) deploy flow; (4) Remote-SSH and agent setup; (5) native AI. No self-hosted CI runner on a public repository.

### P5 NAS and UPS

- **Goal:** durable storage and tested backups. **Depends on:** P2, P4. **Hardware gate:** NAS, UPS.
- **Scope:** NAS operating system chosen by ADR, volumes, backup target, off-site copy, UPS shutdown test, decision on where always-on services run.
- **Exit criteria:** the restore drill passes against the NAS; a simulated power loss shuts down cleanly.

### P6 Network

- **Goal:** DNS, remote access and segmentation. **Depends on:** P5. **Hardware gate:** upgraded network gear.
- **Scope:** internal DNS, VPN in production use, IoT segment, firewall rules, inventory kept current.
- **Exit criteria:** an IoT-segment device cannot reach other zones; remote access works only through the chosen VPN.

### P7 Home automation

- **Goal:** a smart-home hub. **Depends on:** P6. **Hardware gate:** a Linux host and devices; scope not decided.
- **Scope:** to be defined when devices exist (Home Assistant and an MQTT broker are the likely pieces). Not designed yet.

### P8 Personal applications and media

- **Goal:** the everyday applications. **Depends on:** P5 (storage and backups). **Hardware gate:** NAS for media; none for expense and portfolio tracking.
- **Scope:** expense tracking, portfolio tracking, media streaming; each a separate stack chosen by ADR (open source, self-hosted, backed up). Not designed yet.
- **Exit criteria:** each application runs healthy and its data passes the restore drill.

## Claude Code sessions

A session has one verifiable outcome and can be resumed cold: it states its entry state, steps and exit check, and ends with the log updated. Only Now and Next are detailed above; later phases stay outlines until their dependencies are met.

## Dependency order

P0, P1, then P2 and P4 (P4 waits for hardware), P3 after P2, P5 after P2 and P4, P6 after P5, P7 after P6, P8 after P5.

## Risks and assumptions

- Hardware arrives late or in a different order: the laptop phases (P1 to P3) are useful alone.
- CI cannot be made to run: `make check` stays the only proof of checks and required checks stay undecided.
- Single maintainer: work is kept small and documented so it can be resumed.
- A secret or personal detail reaches the public repository: local hooks and CI scanning exist; CI is unproven.
- Assumes the laptop's 8 GB limits what runs beside the VM.

## Updating this roadmap

Version 1.x changes progress or wording; a new major version means the phase structure changed. A phase may be split when it needs more than about five sessions or has two independent exit criteria. Phases are reordered only when a dependency or hardware change makes the current order impossible. Every split or reorder is logged with its reason; any change touching a decided item needs the owner's approval first.

Changelog: 1.0 (2026-10-20): added P8 personal applications and media; restructured into phases with gates, exit criteria and a now/next/later view; CI proof made the first item.
