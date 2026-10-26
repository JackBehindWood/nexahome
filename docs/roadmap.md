# Roadmap

Version 0.1 · Last reviewed 2026-10-26

What gets built and in what order. Hardware has no dates; phases are ordered by dependency. Update this file at the end of every working session.

## Now, next, later

| When | Work |
| :--- | :--- |
| Now | P2.5 is done (sessions 1 to 5): stacks `edge`, `identity` and `portal` exist, Actual is the first client, identity restores and a login works through the restored provider; ADRs 0010 to 0012 stay Proposed; P2 is closed |
| Next | P3 health view, confirmed by the owner 2026-10-26: session 1 (spike and ADR 0013, Proposed) is done; session 2 builds the stack. The portal is the only health view until then |
| Later | Health view (P3), then the hardware phases in order: Mac mini, NAS and UPS, network, home automation, then personal applications and media |

Pending owner actions are tracked in the [session log](session-log.md), not here.

## Done

- **Session 0, bootstrap:** repository, documents, decisions table, first ADRs, licence, README, SECURITY.
- **Session 1, pipeline proof:** Makefile, project-local tooling, opt-in pre-commit hook, Colima runtime, `hello` stack, Compose policy check, CI workflow file, PR template.
- **Session 2, publish safely (done except the pending items):** history scan, public repository, secret scanning and push protection, `main` protected. CI was proven afterwards (first run 2026-10-20) once Actions was enabled.
- **Documentation foundation:** this documentation set, version 0.1.
- **P2 session 1, stack contract and first app:** stack template, volume-label and project-name checks, Makefile conventions, `.env` bootstrap, `actual` stack, add-a-stack runbook (ADRs 0007 and 0009 Proposed).
- **P2 session 2, backup:** restic one-shot stack, `make backup-init`, `make backup`, `make status`, one-shot exception in the Compose check (ADR 0008 Proposed; backup run and checked by the owner, restore not tested).
- **P2 session 3, restore drill:** `make restore` (never overwrites), fingerprint helper, restore runbook, two drills passed on the laptop (fresh-clone restore and delete-and-restore in place), update steps in the README. Cut with a trigger: `make upgrade`, changelog, separate upgrade runbook. Backup tool ADR 0008 still Proposed.
- **P2.5 Identity, edge and portal:** edge, identity and portal stacks, Actual as first OIDC client, recovery and test-sign-in runbooks, `make smoke`, `make verify`; restore drill passed 2026-10-23 and found that identity had not been backed up (fixed).
- **Entry points (docs only):** README as the use entry, CONTRIBUTING as the developer entry, start-here block in the docs index; ADR 0006 awaits the owner's decision.

## Phases

Each phase lists goal, scope, dependencies, hardware gate, exit criteria, verification and definition of done. Done means every exit criterion is verified and the log says so.

### P0 Foundation (done)

Goal: a safe, public, documented starting point. Exit criteria were met by Sessions 0 to 2 except the CI proof, which moved to P1.

### P1 Prove CI and the publishing flow

- **Status:** CI proof and merges are done (2026-10-20); Dependabot is configured (`.github/dependabot.yml`, weekly: Actions, the hello stack image, dev tools). The CI checks `secrets` and `checks` are required on `main`. Dependabot reads its config from the default branch, so it starts once `dev` is merged into `main`.
- **Goal:** a green CI run, and a working merge path. **Depends on:** P0. **Hardware:** none.
- **Scope:** find why no workflow run starts and fix it; add a manual trigger if that is the cause (owner approval for the workflow change); merge pull request 1 into `dev`, then `dev` into `main` by pull request (owner approves each merge); decide whether to require the CI checks on `main`; add `.github/dependabot.yml` for Actions and image tags.
- **Exit criteria:** one successful CI run is linked in the log; `main` and `dev` match; the required-check decision is in the register; Dependabot's config is validated by GitHub.
- **Verification:** `gh run list`, `gh api` on branch protection, `git log`.
- **Sessions:** (1) CI proof; (2) merges; (3) Dependabot.

### P2 Persistence and restore drill

- **Goal:** prove the backup model on the laptop. **Depends on:** P1 (CI proof). **Hardware:** none.
- **Scope:** one real stateful stack (a small database or file service), a backup using the chosen tool (restic is the shortlist, chosen by ADR), a tested restore, a first runbook for restore, a short "add a stack" section.
- **Exit criteria:** data deleted on purpose is restored from backup and checked; the runbook was followed by someone cold; `make check` passes.
- **Verification:** restore drill output recorded in the log. The VM stays at 2 GB, so one extra light stack at a time.
- **Sessions:** (1) stack with a named volume (done); (2) backup (done, see session log); (3) restore drill and runbook (done). The owner did the cold read of the restore runbook on 2026-10-21 and found it good, so P2 is closed.

### P2.5 Identity, edge and portal

- **Status:** done 2026-10-23 (closed). Sessions 1 (spike) and 2 (edge and identity stacks) done 2026-10-22, session 3 (Actual as client, refusals, recovery runbook), session 4 (portal, four-step contract, `make smoke`) and session 5 (backup and restore drill, `make verify`) done 2026-10-23; all design choices are Proposed (ADRs 0010, 0011 and 0012). Chosen design: Pocket ID's My Apps page is the one sign-in page; the portal is an open read-only status board on loopback; agents have no account yet.
- **Goal:** one login for NexaHome apps with two roles (admin, user) and a reserved role for AI agents that is never admin, plus a launchpad with a health dot per stack. **Depends on:** P2 (backup and restore; closed). **Hardware:** none.
- **Scope:** a small OIDC identity provider in its own stack, a reverse-proxy edge stack with local hostnames on a shared network, Actual Budget as the first client (password login kept as fallback), a read-only portal without Docker socket access, and a recovery runbook. Own expense app as a client waits for P8; forward-auth, LDAP, mail, agent tokens, public TLS and uptime history are deferred (P3, P6, P8).
- **Exit criteria:** both roles log in to Actual through the provider and a non-member is refused; the recovery runbook was followed once with the admin passkey treated as lost; the provider is backed up and restored with `make backup` and `make restore`, and a login works through the restored provider; the three new stacks fit the measured RAM budget on the 2 GB VM; `make check` passes.
- **Verification:** drill output and RAM figures recorded in the session log and the ADRs.
- **Sessions:** (1) spike and ADRs; (2) edge and identity stacks; (3) Actual as client and recovery runbook; (4) portal; (5) backup and restore drill, close. Done: 1, 2, 3, 4, 5. The step-by-step plan is local to the owner's machine.

### P3 Health view

- **Status:** confirmed by the owner 2026-10-26. Session 1 done: Gatus and Uptime Kuma measured, [ADR 0013](adr/0013-health-view.md) Proposed (Gatus). Session 2 not started.
- **Goal:** one place to see service health, history and notifications. Logs stay with `docker compose logs`: without the Docker socket no tool can show them (Proposed, ADR 0013). The launchpad (central dashboard) moved to P2.5. **Depends on:** P2 (a real service to watch). **Hardware:** none.
- **Scope:** compare two tools from the [shortlist](observability.md#tool-shortlist), choose by ADR, deploy as a stack; link it from the P2.5 portal.
- **Exit criteria:** it shows the real stack's state; stopping the tool breaks nothing else (decoupling rule).
- **Sessions:** (1) spike and ADR (done); (2) stack, browser checks and restore-drill decision. Split with the owner's agreement on 2026-10-26: the spike and ADR come first, nothing is built before the ADR exists.

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
- **Scope:** expense tracking, portfolio tracking, media streaming; each a separate stack chosen by ADR (open source, self-hosted, backed up). Not designed yet. The own expense app is a client of the P2.5 identity provider and holds no login code of its own.
- **Exit criteria:** each application runs healthy and its data passes the restore drill.

## Claude Code sessions

A session has one verifiable outcome and can be resumed cold: it states its entry state, steps and exit check, and ends with the log updated. Only Now and Next are detailed above; later phases stay outlines until their dependencies are met.

## Dependency order

P0, P1, then P2 and P4 (P4 waits for hardware), P2.5 after P2, P3 after P2.5 (the portal links it), P5 after P2 and P4, P6 after P5, P7 after P6, P8 after P5.

## Risks and assumptions

- Hardware arrives late or in a different order: the laptop phases (P1 to P3) are useful alone.
- CI stops running (for example Actions disabled again): `make check` stays the local proof.
- Single maintainer: work is kept small and documented so it can be resumed.
- A secret or personal detail reaches the public repository: local hooks and CI scanning exist.
- Assumes the laptop's 8 GB limits what runs beside the VM.

## Updating this roadmap

Version 0.x while the project is pre-release: changes to progress or wording keep the number; 1.0 is reserved for the first release tag. A phase may be split when it needs more than about five sessions or has two independent exit criteria. Phases are reordered only when a dependency or hardware change makes the current order impossible. Every split or reorder is logged with its reason; any change touching a decided item needs the owner's approval first.

Changelog: 0.1 (2026-10-26): P3 confirmed, session 1 done, P3 split into two sessions; 0.1 (2026-10-23): P2.5 session 5 done, P2.5 closed, next P3; 0.1 (2026-10-23): P2.5 session 4 done; 0.1 (2026-10-23): P2.5 session 3 done; 0.1 (2026-10-22): P2.5 sessions 1 and 2 done, Now and Next rows; 0.1 (2026-10-21): P2 closed after the owner's cold read of the restore runbook; 0.1 (2026-10-21): Now and Next rows after all four ADR decisions; 0.1 (2026-10-21): Now row after ADR decisions; versioning rule for 0.x; version renamed from 1.0; 0.1 (2026-10-21): P2.5 added (identity, edge, portal; owner approved), launchpad moved from P3, P8 note; 0.1 (2026-10-21): P2 session 3 done; 0.1 (2026-10-21): ADR 0008 in the Now row, S3 branch noted; 0.1 (2026-10-21): P2 session 2 done; 0.1 (2026-10-21): P2 session 1 done; 0.1 (2026-10-21): Now row corrected (merges done), entry-points work recorded; 0.1 (2026-10-20): P1 status; added P8 personal applications and media; restructured into phases with gates, exit criteria and a now/next/later view; CI proof made the first item.
