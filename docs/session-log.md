# Session Log

Newest first. Each entry: done, doc changes with reasons, next, open questions.

## 2026-10-22: P2.5 session 2, edge and identity stacks

**Done**
- Branch `feat/p2-5-s2-stacks` (commit `8789ec2`, not pushed). Part A design review first; the owner chose: Pocket ID's My Apps page as the one sign-in page, the portal stays an open read-only status board on loopback, agents rule only (no account), clients registered by hand in the UI, no static API key, secrets auto-generated.
- Built `stacks/edge` (Caddy 2.11.7, 404 catch-all, hardening headers, limits, log rotation) and `stacks/identity` (Pocket ID v2.18.0-distroless). `make up` creates `nexahome-edge`, starts edge and identity first and replaces `GENERATE` values in a new `.env` (never printed). `check_compose.py` rejects other external networks, `cap_add` other than `NET_BIND_SERVICE` and a Docker socket mount; shown failing on mutated copies, then passing. Dependabot entries added.
- Run on Colima (existing profile, started and stopped; images pulled: Caddy and Pocket ID; network `nexahome-edge` created and left in place). Measured: edge 10 MiB, identity 16 MiB idle, images 89 and 110 MB. `/health` 200, foreign `Host` 404, issuer `http://id.nexahome.localhost:8088`. Both run non-root, read-only, all capabilities dropped (edge keeps the flagged `NET_BIND_SERVICE`). `make down` then `make up` kept users, config and images. Restart count 0 after about 40 minutes.
- Browser (owner): first admin and passkey; a second passkey was refused (same iCloud Keychain, one authenticator) and skipped. Audit log shows `PASSKEY_ADDED`, `SIGN_IN` (admin) and `TOKEN_SIGN_IN` (user). The owner reported that `user` sees only Actual Budget and `admin` also sees the admin-only test client; both launch links gave the edge's 404 (no route yet, expected).
- Instance configured with a UI-created API key (named, expiring 2026-11-21), pasted into chat by the owner: app name `NexaHome`, session 1440 minutes, landing page My Apps, groups `admin`, `users`, `agents`, users `admin`, `user`, `agentx` (no passkey), clients `actual` (placeholder) and a temporary `admintest` (deleted). Logos (light, dark, favicon, email, default profile picture) drawn as SVG and uploaded; the owner uploaded the background. Key revoked through the API (a call then returned 401) and the local key file deleted.
- Deviation to report: the API key was pasted into the conversation, so it exists in the transcript; it is revoked.

**Doc changes and reasons**
- ADRs 0010 and 0011 amended in place (both still Proposed, so editing is allowed): option chosen, access tiers, agent path and API key contract (Open), 404 catch-all and threat model, what was built and measured, portal gating added to the leaving-loopback gate, advisory check and recovery-token caveat. `project.md`: two Proposed rows (identity provider, edge). `constraints.md`: the `cap_add`, socket and external-network rules are now enforced; `GENERATE` placeholder documented. No Confirmed decision was touched.
- New READMEs for both stacks with measured RAM and disk, first-run steps, client field table and the host-side recovery command.
- Not done on purpose: `make secret` (replaced by `GENERATE`), a registration script, `STATIC_API_KEY`, tile or alias drift checks.

**Verification**
- `make check` passed (hooks and the Compose policy for all six stacks); nothing staged; the commit holds no `.env`, key, `data/` or the API key (scanned).
- **Not verified:** a second passkey; Chrome, Firefox, Linux; restore of the identity volume (S5); the favicon and email logo in a real browser; `agentx` refusal, Actual's OIDC login and Actual boot with edge or identity down (S3); whether the S1 Pocket ID exit recurs (not seen in about 40 minutes); session length effect; whether the one-day session is accepted by Actual; CI for this branch (not pushed). My Apps and the role view are as reported by the owner.

**Next:** P2.5 session 3: Actual as the first client (route and alias on the edge, client secret, OIDC variables, password fallback kept), refusals for a non-member and `agentx`, boot order with edge or identity down, `docs/runbooks/identity-recovery.md` followed once.

**Open questions**
- A paid tier would touch the Confirmed rules on open source and no subscriptions: owner decision when it becomes real.
- Image digests for all stacks (tag plus digest)?
- A real second authenticator (phone or security key) before real data exists.
- Pocket ID `v2.18.0` or a later patch: Dependabot will propose; the agent path needs a newer release (not verified).

**Pending (owner)**
- Run nothing for the key: confirm in Settings, API Keys that `s2-config` is gone.
- Approval to push `feat/p2-5-s2-stacks` and open a pull request into `dev`.
- Watch security alerts for `pocket-id/pocket-id` and `caddyserver/caddy` on GitHub.
- Remove `nexahome-edge` and the identity volume only if you want them gone (kept for S3).
- Carried over: Dependabot parsing of the new stack entries; the local `.claude/plans/concerns-and-audiences.md`; GitHub setting "Block command line pushes that expose my email"; Makefile, repository layout and security baseline still Proposed.

## 2026-10-22: P2.5 session 1, spike and decision

**Done**
- Branch `feat/p2-5-s1-spike`. Colima started (existing profile, unchanged) and stopped again. A throwaway Compose project (Pocket ID, Caddy, Homepage, Actual) ran on a temporary network with temporary volumes; all removed, plus the four pulled spike images and one `alpine` image (the existing `actual`, backup and other images were left alone). Nothing was left in the repository tree.
- Measured: all three images run on arm64, non-root, read-only, `cap_drop: ALL` (Caddy needs `cap_add: NET_BIND_SERVICE`, a flagged deviation); idle RAM edge 10 to 15, identity 17, portal 106 to 110 MiB (about 133 to 142 MiB, R6 met); Actual accepts an `http://` issuer and `http://*.localhost` callback; passkey works in Safari; groups, client and secrets can be seeded through the API; group restriction only applies with `isGroupRestricted: true`; non-members and an `agents` member are refused by the provider; the recovery token command works; Homepage `siteMonitor` through the edge alias shows 200 and 502.
- Surprises: Pocket ID exited once after about 35 minutes (cause unknown); its distroless image has no `/app/data`, so the volume is mounted at the image's non-root home directory; my own seeding left the client unrestricted until the flag was set; Actual refuses with a generic "Something went wrong".
- Deviation to report: three diagnostic `docker run` calls (one `alpine`, two Caddy) ran as the image's default root user, which the session approvals did not allow. They were short and read-only; I stopped using plain `docker run` after the second and used `--user` or image inspection instead.

**Doc changes and reasons**
- Added `docs/adr/0010-identity-provider.md` and `docs/adr/0011-edge-and-local-hostnames.md`, both Proposed, with the measured figures, failure modes, migration table and leaving-loopback gate. No Confirmed decision was touched.
- Not done on purpose, on the owner's instruction for this session: the `docs/project.md` register rows, the roadmap tick, stacks, Makefile and scripts.

**Next:** the owner reads ADRs 0010 and 0011 and decides the open points below; then P2.5 session 2 (edge and identity stacks) if the design stays.

**Open questions**
- Owner feedback: the sign-in flow felt clumsy and the owner wants one command-centre page to sign in to, usable by an admin and an agent. Decide: gate the portal itself or only the apps; and how an agent signs in (agents must not use passkeys). Or take the cheaper way back: no provider in P2.5.
- Client registration: by hand in the UI or a small script; remove or rotate the static API key afterwards.
- Which claim Actual matches for a second user, and the full second-user path, were not tested.

**Not verified:** a second allowed user logging in to Actual; Chrome and Firefox (not installed); Linux; restore of the identity volume with `make restore`; the cause of the Pocket ID exit; Homepage with a read-only bind-mounted config directory; the daily sign-in experience for two users; browser results are as reported by the owner.

**Still pending (owner)**
- Read ADRs 0010 and 0011; answer the open questions above. Approval to push `feat/p2-5-s1-spike` and open a pull request into `dev`.

## 2026-10-21: P2 closed (docs only)

**Done**
- The owner did the cold read of `docs/runbooks/restore.md` and found it good (no gaps noted). The last open P2 exit item is met, so P2 is closed.

**Doc changes and reasons**
- `docs/roadmap.md`: Next row and P2 and P2.5 lines updated to say P2 is closed. No Confirmed decision was touched.

**Deferred (owner decision):** an extra recovery system for logins (admin-issued recovery as a feature, a master password, an offline paper or split secret). P2.5 session 3 keeps only a second passkey, a host-side one-time token and a password-manager copy of the restic password and the identity encryption key. Revisit when real data exists.

**Next:** P2.5 session 1, the spike and ADRs 0010 and 0011 (needs approval to start the container runtime and pull images).

**Not verified:** the cold read itself (reported by the owner, not observed); CI for this branch (not pushed).

## 2026-10-21: Owner actions closed (docs only)

**Done**
- Owner answers: push `feat/p2-5-plan` only (no pull request yet); ADR statuses left to me; yes to rewording the identity row and amending ADR 0009; documentation version renamed to 0.x.

**Doc changes and reasons**
- ADRs 0007 (stack contract) and 0008 (backup tool) set to Confirmed, and their register rows moved (the backup-tool row from Open). Reason: both are proven by the P2 drills, P2.5 builds on them, and the owner delegated the decision ("you decide"). That is delegation, not a per-ADR yes: the owner can reverse either one. ADRs 0006 and 0009 stay Proposed at this point; later the same day the owner asked to finalise the open items and both were Confirmed too, again by delegation (0009 still reads drill subject only).
- `project.md` and `architecture.md`: the identity row and bullet reworded (still Proposed): sole administrator, roles `admin` and `users`, agent never admin, one small provider planned in P2.5. ADR 0009: one line, Actual is also the first client of that provider.
- Version: documentation headers and changelogs renamed from 1.0 to 0.1; `docs/README.md` and the roadmap say 1.0 is reserved for the first release tag. Reason: the project is pre-release.
- `roadmap.md`: Now row updated for the decisions.

**Not verified:** CI for the branch (pushed, no pull request); rendering on GitHub.

**Still pending (owner)**
- Cold read of `docs/runbooks/restore.md` (closes P2). Approvals for the S1 spike (Colima start, image pulls). Pull request and merge of `feat/p2-5-plan` into `dev` when wanted.

## 2026-10-21: P2.5 planning (docs only)

**Done**
- Planning session for the user system; no stack, script or container was touched. Owner answers: one owner now, two roles (admin, user) and a later agent role that is never admin; provider first; new phase P2.5 with only what is needed.
- Plan written locally (`.claude/plans/p2-5-user-system.md`, not committed): five sessions, requirements with verification, interface contract, failure modes, backup and restore drill.

**Doc changes and reasons**
- `docs/roadmap.md`: P2.5 added after P2 (owner approved the change); the launchpad moved from P3 to P2.5 (P3 keeps health history, logs and notifications); a P8 note that the own expense app is an identity client; Now and Next rows and the dependency order updated. No version bump: the project is still 0.x. No Confirmed decision was touched; `project.md` and the ADRs are not edited yet (new Proposed rows and ADRs 0010 to 0012 arrive with session 1 and later).

**Next:** P2.5 session 1, spike and ADRs (needs approval to start the container runtime and pull images).

**Open questions**
- The docs headers say "Version 1.0" while the project is 0.x; not changed, owner to decide.
- Reword the Proposed register row "Single admin account; no SSO or identity provider until ..." (needs the owner's yes).
- ADRs 0006 to 0009 are still Proposed; P2.5 builds on 0007 and 0008.

## 2026-10-21: P2 session 3, restore drill

**Done**
- On branch `feat/restore` (from `feat/backup`, stacked on `feat/persistence-restore`; none of the three pushed): `make restore STACK= [SNAPSHOT=] [TARGET=]`, `scripts/backup.sh restore` and `fingerprint`, `docs/runbooks/restore.md`, two fixes to the backup job, README section "Back up, restore, update".
- Restore never overwrites: it refuses when the target volume exists, creates the volumes with `docker compose create` (copy-up gives the app's ownership), then runs `restic restore --target / --include --verify` with each new volume mounted at the original path. It restores a missing `.env` from the snapshot (written on the host, never printed). The copy-up flow works for real; no root container was needed or run.
- Drill 1 (non-destructive, lost-machine simulation): fresh local clone, copied repository directory, project `nexahome-actual-clone` on port 5007. Fingerprint of ownership, mode and content equalled the original (F0, 4 files); `.env` restored; the owner saw the known transaction. Refusal with an existing volume checked.
- Drill 2 (destructive, owner approved at that moment): live volume `nexahome-actual_data` deleted, `make restore STACK=actual`, fingerprint equal to F0, `make up`, healthy, the owner saw the known transaction.
- Figures (dummy data, 4 files, same disk): each restore about 2 s; repository 64 KB with 2 snapshots at drill time, 3 after a final backup; `restic check --read-data` clean. Clone, repository copy and drill volumes were removed.
- Surprises: (1) restic exits non-zero when setting metadata on `/data`, the read-only parent of the mount; fixed with a tmpfs `/data` in the job. (2) With `user: "1001"` restored files got gid 0, found by the fingerprint, not by `--verify`; the job now runs as `uid:uid`. (3) A backup taken after both fixes works (`make backup`, snapshot saved, check clean).
- Branch order for the merge, by pull request into `dev`, one at a time with base `dev` (CI only runs for pull requests based on `main` or `dev`, and a changed base does not start a run): `feat/persistence-restore`, `feat/backup`, `feat/restore`. At session end nothing is pushed.

**Doc changes and reasons**
- Audit cuts agreed with the owner: `make upgrade`, `CHANGELOG.md`, a compatibility rule in CONTRIBUTING, `compose.override.yaml` in `.gitignore`, and a separate `upgrade.md` (nothing uses them before a release tag or an outside adopter; update is three commands in the README, rollback is in the restore runbook). The upgrade rehearsal waits for the first Dependabot bump of `actual`. `INPLACE=1` was dropped for the same reason of safety: restore never deletes. Drill 1, the swap test and the clean-clone test were run as one.
- `docs/adr/0008-backup-tool.md`: drill evidence and the two fixes; still Proposed (the owner chose to decide it at the merge review). `architecture.md`: Layer 4 and backup paragraph (the drill passed on the laptop's own disk). `docs/README.md`: runbooks row. `stacks/backup/README.md`, `stacks/actual/README.md`, `README.md`: restore command, measured figures, verify step. No Confirmed decision was touched; `project.md` was not edited (register row "Backup tool" stays Open).
- `.claude/plans/p2-persistence-restore.md` (local) now records the S2 and S3 deviations.

**Verification**
- `make check` passed; relative links resolve; failure paths of `restore` tested with a fake `docker` (no argument, unknown stack, runtime down, missing repository, no snapshot, existing volume); `git diff --staged` held no `.env`, key, `data/` or `.config/`. Colima was started for the drills and stopped by the owner at the end.
- **Not verified:** CI for these branches (not pushed); Linux and `dash`; a real external disk; stacks with a UID other than 1001; large data or restore time at scale; an interrupted restore; the cold read of `restore.md` (the owner does this); an upgrade with an older Actual tag; Actual outbound calls; Dependabot parsing the new entries.

**Next:** merge the three branches into `dev` by pull request (S1, S2, S3, each pushed, opened and merged on the owner's approval), then decide ADRs 0006 to 0009. After that: a planning session for a user system (P2.5, owner's direction: there is no user or identity layer yet; build it, keep Actual as a stand-in app, later replace it with the owner's own expense app), then P3 (health view). P2 closes when the owner has done the cold read of the restore runbook.

**Open questions**
- Accept, change or reject ADR 0008 (backup tool; the drill evidence is in it), and ADRs 0006, 0007, 0009 (0009 reads "drill subject only").
- Where the restic password copy is kept (not decided; dummy data only until then). Real data waits for that and for a second copy.
- User system (P2.5): scope and whether it is a new phase are not decided. The documents currently say no identity provider until a second user or about three apps with logins ([architecture](architecture.md#secrets-and-identity)); the owner wants it planned before the own expense app. The planning session decides, by ADR, and changes the roadmap only with the owner's approval.

**Pending (owner actions, not actioned)**
- Cold read of `docs/runbooks/restore.md`: follow its first block once on the drill volume and note gaps.
- Merge approvals: push, pull request and merge for each of the three branches, in order (asked one by one in the next step); merges into `main` are out of scope.
- Local `.claude/settings.json`: allow `make status`, `make snapshots`; ask for `make backup-init`, `make backup`, `make restore`.
- The live volume `nexahome-actual_data` holds dummy data, and `data/backup` holds the test repository (`rm -rf data/backup .config` removes both).
- Carried over: Dependabot parses under Insights, Dependency graph, Dependabot (includes `stacks/actual` and `stacks/backup`); delete the dummy `.env` in the working folder by hand; GitHub setting "Block command line pushes that expose my email"; Makefile, repository layout and security baseline still Proposed; delete the local plan `.claude/plans/concerns-and-audiences.md`.

## 2026-10-21: P2 session 2, backup

**Done**
- On branch `feat/backup` (from `feat/persistence-restore`, because session 1 is not merged into `dev`, by the owner's instruction; not pushed): spike, ADR 0008 (Proposed), `stacks/backup` (restic 0.19.1, one-shot), `scripts/backup.sh` (POSIX), `make backup-init`, `make backup`, `make status`, one-shot exception in `check_compose.py`, Dependabot entry.
- Spike with Colima started and stopped afterwards: arm64 image exists; backup as uid 1001 into a host directory under `$HOME` works, second run added 350 B, `restic check` clean; a mode 600 host file is readable by the container; a directory outside `$HOME` is silently not shared (the repository would end up inside the VM), so `make backup-init` verifies the repository on the host; an extra writable Colima mount works but replaces the `$HOME` default and is saved in `~/.colima/default/colima.yaml`; restore as non-root into a fresh volume fails, and works after the volume is initialised from the app image (copy-up), so no root container was needed or run.
- Spike leftovers removed: test volumes, scratchpad and `$HOME` test directories; `colima.yaml` mounts set back to `mounts: []` after the test.
- Script failure paths tested with a fake `docker` (runtime down, password missing or world-readable, repository missing, status states, no overwrite on init). `make check` passes; the one-shot rule fails on a copy without the label.

**Doc changes and reasons**
- `constraints.md`: one-shot exception to the health check and restart rules (the job is run by a script, not kept up). `architecture.md`: backup model and layer 4 state. `roadmap.md`: session 2 done, next set. ADR 0008 is Proposed; the register row "Backup tool" stays Open until the owner says yes. ADR 0004 and `project.md` were not edited.
- Owner decision after the build: the password file defaults to a gitignored `.config/restic-password` inside the working copy instead of the home directory (override: `NEXAHOME_RESTIC_PASSWORD_FILE`). `make backup-init` refuses a path inside the repository that is not gitignored.
- Trade-off recorded in ADR 0008: deleting the working copy deletes the password, so the separate copy matters more.
- The repository directory followed: default `data/backup` (gitignored, visible, size in `make status`) instead of `~/.local/share`; a Docker volume was rejected (hidden in the 20 GB VM disk, lost with `colima delete`). `backup-init` applies the gitignore guard to both paths.
- Owner direction: Actual is a throwaway drill subject; an own expense app is planned for P8. ADR 0009 (still Proposed) and its register row say so. Also added `make snapshots` and `scripts/backup.sh restic <args>` after the owner hit a missing-variable error running restic by hand.
- Audit cuts from the P2 plan (owner agreed): no "newer tag" in status, no 7-day nudge in `make up`, no `scripts/stacks.py` (status is shell, backup age comes from the repository's `snapshots/` files), restore flags and fingerprint helper left to session 3. Added: fixed host name so runs are incremental; `.env` of a stack is saved only when the stack has a labelled volume.

**Not verified**
- Final check at session end: `make check` passed; relative links resolve; no `.env`, key, `data/` or `.config/` is tracked or staged; `data/` and `.config/` were deleted by the owner after the test; Colima is stopped. CI is not stated here because the branch is not pushed.
- Verified by the owner at the end of the session: `make backup-init`, `make backup` twice (first run saved 111 KiB; second added 684 B, so incremental), `restic check` clean, Actual stopped, backed up, restarted and healthy again, refusal with a missing repository and with a password file open to others, `make status`. Cleanup with `rm -r` prompted per file because restic files are read-only; the README now says `rm -rf data/backup .config`.
- Restore (session 3); stacks with a UID other than 1001; Linux; a real external disk and macOS permission prompts for it; an interrupted backup; CI for this branch; Dependabot parsing the new entry.

**Next:** P2 session 3: restore drill (`make restore`, fingerprint helper, runbook, upgrade). Test the copy-up restore flow there.

**Open questions**
- Accept, change or reject ADR 0008 (backup tool); then the register row can move. Also still open: ADRs 0006, 0007 and 0009 (0009 now reads "drill subject only").
- Where the restic password copy will be kept (not decided; dummy data only until then).
- Branch order: S1 (`feat/persistence-restore`) and S2 (`feat/backup`) are stacked and unmerged; S3 is planned on `feat/restore` from `feat/backup`. Merge order will be S1, then S2, then S3, each by pull request into `dev`.

**Pending (owner actions, not actioned)**
- Local `.claude/settings.json`: allow `make status` and `make snapshots`; ask for `make backup-init` and `make backup`. Local plan deviations for S2 and S3 (restic host name, `.config/`, `data/backup`, copy-up restore, no root container) are not written to `.claude/plans/p2-persistence-restore.md` yet.
- Push the three stacked branches and open pull requests into `dev` when ready; decide ADRs 0006 to 0009.
- Start S3: first a fresh `make backup-init` and `make backup`, run by the owner.
- Carried over: Dependabot parses under Insights, Dependency graph, Dependabot (now includes `stacks/backup`); delete the dummy `.env` in the working folder by hand; GitHub setting "Block command line pushes that expose my email"; Makefile, repository layout and security baseline still Proposed; delete the local plan `.claude/plans/concerns-and-audiences.md`.

## 2026-10-21: P2 session 1, stack contract and first app

**Done**
- On branch `feat/persistence-restore` (from `dev`, not pushed): `stacks/_template/`; two new `check_compose.py` rules (volume label `nexahome.backup`, project name `nexahome-<directory>`); Makefile rewritten with help grouping and `up`/`down`/`ps` over all stacks; `.env` bootstrap that stops on `CHANGE_ME`; `stacks/actual` (Actual Budget 26.10.0-alpine); `docs/runbooks/add-a-stack.md`; Dependabot entry for `actual`; ADRs 0007 and 0009 (Proposed). ADR 0008 is reserved for the backup tool (session 2).
- Showed `make check` failing on scratchpad copies (unlabelled volume; wrong project name), then passing.
- With Colima started (2 CPU, 2 GB, 20 GB) and stopped afterwards: `make up` brought both stacks healthy; Actual runs as uid 1001 with a read-only root and writes `/data`; the README quick start was run as written; `make down` kept the volume `nexahome-actual_data`.
- Measured with both stacks running: Actual 130 MiB, hello 3 MiB, VM 419 of 1959 MiB used, VM disk 1.2 of 19 GB.

**Doc changes and reasons**
- `constraints.md`: label, project-name and placeholder rules; a Makefile conventions section (the deferral in ADR 0006 now points there; ADR 0006 is Proposed, so its one line was edited). Reason: conventions enter the docs and the Makefile together.
- `project.md`: two Proposed rows (stack contract, first app); no existing row edited. `architecture.md`, `roadmap.md`, `docs/README.md` (runbooks row), `README.md` (quick start is now `make up`), `CONTRIBUTING.md` (runbook link): to match what exists.
- Decision this session: run-path code is Make and POSIX shell, checks are Python; a shared `scripts/stacks.py` is extracted when a second Python consumer appears (session 2 or 3). No compiled tooling.
- HTTPS/TLS and a reverse proxy stay deferred (trigger: first service reachable beyond `127.0.0.1`, P4 or P6).

**Not verified**
- Outbound network calls by Actual; behaviour across image upgrades; the Linux path; CI for this branch (not pushed); Dependabot parsing of the new entry; make behaviour beyond GNU make 3.81 on macOS.
- The cold-reader test of the add-a-stack runbook.
- Final check at session end: `make check` passed; link check found no broken relative links; no `.env`, key or `data/` is tracked or staged; working tree clean on `feat/persistence-restore`. CI is not stated here because the branch is not pushed.

**Next:** P2 session 2, backup: spike first (restic arm64 image, Colima mount, restore ownership), then ADR 0008.

**Open questions**
- Accept, change or reject ADRs 0006, 0007 and 0009.
- Where the restic password copy will be kept; whether an external disk is available for the backup directory (needed before session 2).
- Delete the local plan `.claude/plans/concerns-and-audiences.md` (its note says to delete it after this session) and remove the test volume `nexahome-actual_data`, or keep it as the session 2 backup subject.

**Pending (owner actions, not actioned)**
- Push `feat/persistence-restore` and open a pull request into `dev` (S2 needs it merged); decide ADRs 0006, 0007, 0009.
- Done this session by the owner: local allow rules for `make`, `make check`, `make ps`. Local plan, compose rules and `CLAUDE.md` repo map were updated (untracked files).
- Carried over: Dependabot parses under Insights, Dependency graph, Dependabot; delete the dummy `.env` in the working folder by hand; GitHub setting "Block command line pushes that expose my email"; Makefile, repository layout and security baseline still Proposed.

## 2026-10-21: Entry points and instance boundary (docs only)

**Done**
- On branch `feat/concerns-and-audiences` (from `dev`, not pushed): ADR 0006 (Proposed); the root README is now the use entry; CONTRIBUTING is the developer entry; `docs/README.md` has a start-here block and an Audience column; one new Proposed register row.
- Ran the README quick start by hand: with Colima stopped `make up` failed, so a Colima start step was added to the README. After starting Colima, `make up STACK=hello` reached healthy, `make ps` showed `healthy`, the page returned HTTP 200 on `127.0.0.1:8080`; then `make down STACK=hello` and `colima stop`.

**Doc changes and reasons**
- ADR 0006 (Proposed): two entry points and an upstream/instance boundary. Reason: setup steps for developers sat in front of people who only want to run a stack. Deliberately lean: Makefile conventions, new layout directories, the release-tag update promise and an "operating" entry are deferred (to P2 and the first tag) because none exist yet.
- `README.md`: developer setup moved to CONTRIBUTING; prerequisites kept (a runtime is needed to use it); quick start is `make up STACK=hello` because bare `make up` changes meaning in P2; update line says no releases yet, use `main`.
- `CONTRIBUTING.md`: gained developer setup and a note that agent and editor config stays local (ADR 0005).
- `docs/project.md`: one Proposed row added. No existing row was edited; the Confirmed audience and no-hosting rows are refined, not changed, by the ADR.
- `docs/roadmap.md`: Now row corrected (the `dev` to `main` merge was already done); entry-points work recorded; next session set.

**Verification**
- `make check` passed. All `make` targets named in README and CONTRIBUTING exist. Relative links resolve. No `.env`, keys or `data/` in the diff against `dev`. No table row removed or edited in `project.md`.
- **Not verified:** the cold-reader test (needs a fresh session given only README, CONTRIBUTING and `docs/README.md`); rendering on GitHub; CI for this branch (not pushed); the Linux path in the README (no Linux host).

**Next:** P2 session 1, stack contract and first app (local plan; ADR numbers shift by one because 0006 is taken). Branch from `dev` after this branch is merged.

**Open questions**
- Accept, change or reject ADR 0006.
- Push the branch and open a pull request into `dev`? (needs the owner's approval).
- TLS and a reverse proxy are deferred until a service is reachable beyond `127.0.0.1` (P4 or P6).

**Pending (owner actions, not actioned)**
- Decide ADR 0006; push `feat/concerns-and-audiences` and merge into `dev` by pull request.
- Carried over from 2026-10-20, status unconfirmed in this session: Dependabot parses under Insights, Dependency graph, Dependabot; delete the dummy `.env` in the working folder by hand; GitHub account setting "Block command line pushes that expose my email".
- Still Proposed and undecided: Makefile, repository layout, security baseline; optional SSH-signed commits.

## 2026-10-20: Documentation foundation (version 1.0)

**Done**
- Rewrote the documentation set as version 1.0 on branch `feat/docs-foundation`, based on `feat/session-2` because pull request 1 is unmerged: `project.md`, `constraints.md`, `observability.md`, `architecture.md`, `roadmap.md`, `README.md`, `SECURITY.md`; added `docs/README.md` (index, ownership, conventions) and ADR 0005; added an optional `Supersedes` line to the ADR template.

**Doc changes and reasons**
- `project.md`: working-method and metadata sections removed (duplicates; one referred to a local file); decisions regrouped; rows added for frugality, single owner, best-effort availability, audience, hardware order, backup tool, Dependabot, documentation conventions. Reason: one home per fact, and the owner's confirmed constraints were missing.
- `constraints.md`: frugality, tooling policy and the Compose policy now live here (the policy was only in local files and the checker). Tailscale/WireGuard preference removed because it is not decided.
- `architecture.md`: added failure domains, trust zones, backup and restore, identity, migration paths and a capability table; the "SSH key-only" statement removed because the method is not decided.
- `observability.md`: aspirations cut; testable phase 0, shortlist and inventory template added.
- `roadmap.md`: sessions restructured into phases with gates and exit criteria; CI proof is the first item.
- `README.md`: "no services yet" corrected, quick start added. `SECURITY.md`: private reporting is not enabled on the repository, so the text gives a fallback.
- Later in the session: added the full planned-services list, P8 (personal applications and media), notifications and the open-source, no-subscription rule (Confirmed on the owner's yes). Private vulnerability reporting was enabled.
- Status change: "agent configuration stays local" moved from Proposed to Confirmed on the owner's answer "stay local" (ADR 0005). Makefile, repository layout and the security baseline remain Proposed because the owner did not say yes. No other Confirmed item was altered.

**Verification**
- See the verification results reported at the end of this session (links, headers, personal data, duplication, register and ADR cross-check).
- **Not verified:** CI (never ran); Mermaid rendering (needs GitHub); that private vulnerability reporting accepts a real report (enabled, not tested); whether ask rules prompt for container commands; the Action pins in `ci.yml`.

**Next:** Phase P1 in the roadmap: CI proof, then the merges (owner approval), then Dependabot.

**Update, later the same day:** GitHub Actions had been disabled for the repository. After the owner enabled it, CI ran for the first time on pull request 3: jobs `secrets` and `checks` both succeeded. Pull requests 1 to 3 were merged into `dev`; `dev` was then merged into `main` by pull request.

**Pending (owner actions, not actioned)**
- Done by the owner: `secrets` and `checks` are required on `main`.
- Dependabot added (`.github/dependabot.yml`); confirm under Insights, Dependency graph, Dependabot that it parses.
- Delete the dummy `.env` in the working folder by hand.
- GitHub account setting "Block command line pushes that expose my email".
- Private vulnerability reporting was enabled afterwards (done; `SECURITY.md` updated).
- Ask rules for `docker compose up` and `docker run`: confirmed on 2026-10-20, the owner was asked to approve both (done).
- Optional: SSH-signed commits; decide Makefile, repository layout and security baseline (Proposed).

## 2026-10-20: Session 2, Publish safely

**Done**
- Pre-push checks: full-history scan found no personal terms, private IPs, home paths or secrets; detect-secrets clean on all tracked files; one author, the noreply identity; basic web search found no existing "NexaHome" project (not a trademark search).
- Merged `feat/session-1` into `dev` and `dev` into `main` (fast-forward, owner-approved), created the public repo `JackBehindWood/nexahome` (MIT), pushed `main` and `dev`.
- GitHub secret scanning and push protection are enabled (the default for public repos).
- The first push did not start a CI run, so the CI proof goes through a pull request from `feat/session-2` into `dev`.

- Branch protection on `main` (owner's rule: merges to `main` only via PR): PR required with 0 approvals (solo project), enforced for admins, force-push and deletion blocked. Read back via the API; not tested with a real push, because a failed test would have altered `main`. Outsiders contribute through fork PRs; no extra protection on other branches.
- Doc changes: ADR 0002 and the decisions table now state the PR-only rule; added an Open row for required CI checks.

**Not verified / open**
- **CI has never run**: after about 10 minutes, no workflow run exists for either the push or PR #1, with no GitHub incident reported and Actions enabled. Likely a GitHub-side or account-level matter (check the repo's Actions tab). Until a run succeeds, `make check` is the only proof of the checks; required status checks on `main` stay Open.
- PR #1 (`feat/session-2` into `dev`) is open and not merged; merging into `dev` needs the owner's approval. `main` does not yet contain the Session 2 log.
- Owner action: GitHub setting "Block command line pushes that expose my email".

## 2026-10-20: Session 1, Pipeline proof

**Done**
- Tooling: `Makefile` (setup, hooks, unhooks, check, up, down, ps), `requirements-dev.txt` (pre-commit 4.7.0, pre-commit-hooks 6.0.0, detect-secrets 1.5.0), `.venv` created with uv (pip fallback in `make setup`). All hooks are local and run from `.venv`, so nothing is cloned or cached outside the repo.
- Hooks: secrets, private keys, large files, YAML, whitespace, no direct commits to `main`/`dev`, and a personal-data check (private IPs, home paths, `.local` hosts, terms from a local gitignored `.personal-denylist`). The git hook is installed (approved); `make unhooks` removes it.
- Runtime: Colima (already installed) started with 2 CPUs, 2 GB RAM, 20 GB disk. ADR 0004.
- Stack `stacks/hello` (BusyBox httpd, non-root, read-only, caps dropped, health check, bound to `127.0.0.1`), `scripts/check_compose.py` enforcing the compose policy, `.editorconfig`, `.gitattributes`, lean CI (`.github/workflows/ci.yml`, actions pinned to commit SHAs) and a PR template.
- Identity fix: the account predates 2017, so the commit email is now `ID+handle@users.noreply.github.com`; the single unpushed commit was rewritten.
- Local-only by owner's decision: `.claude/`, `CLAUDE.md` and `.vscode/` are gitignored and untracked. Local `.claude/rules/compose.md` and `.vscode/` files exist on this machine only.

**Doc changes and reasons**
- `project.md`: decisions table gained rows for Colima (Confirmed), uv-optional Python tooling (Confirmed), `.vscode/` never committed (Confirmed), and `.claude/` never committed / `CLAUDE.md` local for now (Proposed for `CLAUDE.md`); the working-method pointer no longer links to the untracked `CLAUDE.md`.
- `constraints.md`: guardrails are described as implemented in a local, uncommitted settings file.
- `roadmap.md`: Session 1 marked done; the Session 5 note about settings travelling via git was corrected (they do not); the stack is `hello`, not `whoami`; the "data volume survives restart" exit criterion was dropped (a volume is Session 3 scope).
- No Confirmed decision was altered.

**Verification**
- `make check` passes. Planted fake secret, private IP, home path, `.local` host and a denylist term were each caught; a real commit attempt with a planted secret was blocked; committing on `dev` is blocked.
- `make up`: container healthy, HTTP 200 on `127.0.0.1:8080`, port bound to 127.0.0.1 only, runs as uid 10001, no answer on the LAN address; `make down` clean.
- Permission rules observed: `sudo`, `rm -rf`, `git push --force` and a Read of `.env` were denied; Read of `.env.example` worked; `docker ps`, `docker compose config` and `docker compose ps` ran silently. `rm .env` was also denied.
- **Not verified:** CI (needs a push); whether `docker compose up` / `docker run` raised a prompt (not observable by the agent); the sandbox was not enabled (decision: stay off for now, Proposed).
- A dummy `.env` with a fake value remains in the repo folder (gitignored); the deny rule stopped the agent from deleting it, so delete it by hand.

**Next:** Session 2, publish safely (see `roadmap.md`).

**Open questions**
- Sandbox on or off (Proposed: off for now).
- Name-collision check for "NexaHome".
- Optional SSH-signed commits; macOS version and RAM.

## 2026-10-20: Session 0, Bootstrap

**Done**
- Initialised git (branch `main`), moved the four docs into `docs/` and renamed `PROJECT.md` to `docs/project.md` (lowercase consistency).
- Wrote `CLAUDE.md` (from the old `INSTRUCTIONS.md` persona and rules, tightened), `.claude/settings.json`, skills `/session-end` and `/adr`.
- Added `.gitignore`, `.env.example`, `LICENSE` (MIT, "NexaHome contributors"), `README.md`, `SECURITY.md`, ADRs 0001-0003, `docs/roadmap.md`, this log.
- Removed `INSTRUCTIONS.md` (never committed; its content lives in `CLAUDE.md`).
- Repo-local git identity: GitHub handle with noreply address. Nothing pushed, no remote.
- Found that the owner's global gitignore excludes `CLAUDE.md` and `.claude/`; the repo `.gitignore` now re-includes them (the global file was not touched). The first commit initially missed them and was amended before anything was shared.

**Doc changes and reasons**
- `project.md`: replaced "Open source" with MIT; added platform-independence goal and non-goals; reworded "seamlessly" to "with documented migration steps"; replaced the Working Method section with a pointer to `CLAUDE.md` (it duplicated `INSTRUCTIONS.md` and `constraints.md`); added a decisions table with status labels (statuses taken from your answers; layout, security baseline, Makefile left Proposed); added a current-status pointer.
- `architecture.md`: made Layer 3 host-agnostic; added a hosts table and resolved the Mac mini over-assignment (always-on services belong on the NAS/server); noted containers on macOS cannot use the GPU or USB so local AI runs natively; added terms, capability table, data-placement section, and three lines on remote access (SSH goal confirmed, method open).
- `constraints.md`: added the platform-independence principle; marked Docker Compose as the firm choice and everything else a preference; made reliability checkable; removed Ansible, gRPC and OIDC from preferences; added public-repo rules and the `127.0.0.1` binding default; added the guardrail enforcement table with its limits; backups line now says restore drills use a local volume until a NAS exists.
- `observability.md`: asset inventory must stay private (public repo); added a Phase 0 for the laptop.
- No Confirmed decision was altered. Cut from the plan: glossary file (terms defined in `architecture.md`).

**Verification (all passed)**
- `CLAUDE.md` is 67 lines, uses no `@imports`, and every path it points to exists.
- `.claude/settings.json` parses as JSON; all relative markdown links resolve.
- No personal terms in the tree (only the generic `/Users/...` instruction in `CLAUDE.md`).
- `.gitignore` works for `.env`, `.env.production`, `data/`, `.venv/`, `settings.local.json`, `.DS_Store`; `.env.example` is not ignored.
- **Not verified:** that Claude Code enforces the permission rules as intended (including the `Read(!.env.example)` carve-out) and that the skills load; both are tested in Session 1. No hook or scanner exists yet.

**Next:** Session 1 (see `roadmap.md`).

**Open questions**
- Container runtime (Docker Desktop / OrbStack / Colima), decided in Session 1.
- macOS version and RAM (VM sizing).
- Verify the GitHub noreply address format for the handle before the first push (the legacy form was used; the numeric-ID form may be needed).
- Name-collision check for "NexaHome" before the first push.
- Optional SSH-signed commits.
- Sandbox on or off.
- The first commit exists only on this laptop until a push.
