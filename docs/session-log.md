# Session Log

Newest first. Each entry: done, doc changes with reasons, next, open questions.

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
