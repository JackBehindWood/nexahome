# Session Log

Newest first. Each entry: done, doc changes with reasons, next, open questions.

## Pending owner actions (the one current list)

Last replaced 2026-11-03 (PK6c). Older entries end with a pointer here instead of their own list.

**Decide**
- Other Proposed register rows (documentation conventions, repository layout, task runner, security baseline, roles, three Packaging rows); review ADRs 0014 to 0020, the SSH runbook and the packaging design. Proposed ADR 0018, 0019 and 0020 still carry present-tense claims the code now contradicts (audit S-10): a wording batch for the ADR-update session.
- Rewords that touch Confirmed items: B1, B2 (language rule in the register and ADR 0007), C1, C2 (ADR 0007), D1 (one register row), and audit S-16 and S-25 (stale cross-status wording in ADR 0007 to 0009).
- GitHub: Dependabot alerts and security updates are disabled for the repository (your action, Settings, Code security); the account setting "Block command line pushes that expose my email"; optional SSH-signed commits.
- Open choices: digest pinning; paid tier versus the open-source rule; keep `hello` on the edge and in the portal; delete the root `.env.example` (it holds no setting, audit S-23); the first tag number (the package is 0.2.0, the plan said `v0.1.0`, so `update` would never offer it).

**Git**
- Pull requests 23 and 24 are merged (2026-11-03); `main` requires `checks`, `secrets` and `gate`, branches up to date. `platforms` is never required.
- Dependabot pull requests (all into `main`): 26, 29 and 30 have every job green; 25, 27 and 28 have the required jobs green and a red `platforms` because the macOS leg was abandoned with no step run (the `platforms` job now treats that as "did not run", in PK6c). 28 (pocket-id) stays held. Merging and pushing are your yes; the PK6c commits on `feat/packaging` are not pushed.

**Security hygiene**
- Keep `ENCRYPTION_KEY` and the restic password in a password manager (the repository is on the same disk: a drill, not protection); keep the ntfy topic secret.
- Confirm in Pocket ID that the first Actual client secret and the session 2 key `s2-config` are gone.
- A real second authenticator before real data exists; a permanent outsider test account and one Safari profile per test account ([test-sso](runbooks/test-sso.md)).
- Watch security alerts on GitHub for `pocket-id/pocket-id`, `caddyserver/caddy`, `gethomepage/homepage`, `TwiN/gatus`.

**Open work**
- Diagnose the Pocket ID self-restart; optional admin-only sign-in for the health view.
- `scripts/__pycache__` (untracked, gitignored) is a leftover: delete it (your yes).
- Dependabot parsing is shown for `portal`, `identity`, `gatus` and `pip`; not yet for `github-actions`, `hello`, `actual`, `backup`, `edge`, `_template` (no newer tag is also a reason); the `dev` and `check` dependency groups are unproven until a Dependabot pull request appears after a push.
- Audit rows left for PK7 or later: S-21 (two `.env` creators until `nexahome up`), S-26 (backup job mounts every stack's `.env`), S-30 (deploy checkout and instance share a folder name), the package rows P-07 (trust model of `update`), P-11, P-12, P-14, P-16, P-18 to P-22, P-25 to P-27.

## 2026-11-03: audit planning and Step 0 (between PK6 and PK7)

**Done**
- Read-only Step 0: 383 tests pass on Python 3.13 and 3.14 (also with pytest 9.2.0), `make check` green, the wheel holds exactly the 30 tracked non-README stack files, nothing under `.claude/`, `CLAUDE.md` or `.env` is tracked, CI on `eba6537` passed, PR 23 and 24 are merged. False premise: "`main` lacks `gate`" (it has it).
- `feat/packaging` fast-forwarded to `origin/dev` (0 ahead, 8 behind); not pushed.
- Dependabot 25 to 30 reviewed, rebase requested on five (see Pending, Git); no merge.
- Local plans: audit sessions PK6a to PK6e added to the packaging plan (code, stacks and docs, fixes and compaction, app-stack ADR draft, graphify). Decided by the owner: a constants module (`defaults.py`), a `[dependency-groups] dev` for pytest (single source in `pyproject.toml`), own images only as a Proposed ADR draft first.

**Doc changes and reasons**
- This log: the Git block of Pending refreshed (it still said `main` lacked `gate` and the pull requests were open). `docs/roadmap.md`: Next row. No ADR edited, no row promoted, no code changed.

**Next:** PK6a (read-only code audit), then PK6b, then you name the rows to fix (PK6c).
**Open questions:** stay on `feat/packaging` or branch from `dev`; Go for app stacks (the 2026-11-02 answer said no Go); `requirements-dev.txt` retired or generated.
**Not verified:** hatchling 1.33.0 build, CI on the rebased Dependabot pull requests, release notes read in full, Dependabot support for dependency groups.
**Pending:** the list at the top.

## 2026-11-03: PK6 (init, config, packages by concern, the 5-minute path)

**Done** (18 commits on `feat/packaging`)
- `nexahome init [DIR]` (default `~/nexahome`): copies the bundled stacks, writes `nexahome.toml` (`hello` enabled) and `.nexahome/manifest.json` (sha256 per file). Refuses a non-empty folder and anything inside a clone or instance; never overwrites; writes no `.env`; files 0644 and folders 0755 whatever the umask; a failed write removes only what that run made. `nexahome config list|get|set stacks`: strict reader (unknown key, wrong type, bad TOML, unknown stack, newer schema each end in one command), atomic write. Home resolution: `--home`, `$NEXAHOME_HOME`, nearest parent with `nexahome.toml` or `stacks/` plus a Makefile, else `~/nexahome` if it holds a `nexahome.toml`. In an instance `env` ends in the commands that start the stacks.
- Packages by concern (owner request): `docker/` (all Docker CLI knowledge; a test keeps `"docker"` and the edge network name out of other modules), `instance/`, `stacks/`, `release/`; a test keeps them from importing `commands/`. Error-message pass: `check` with nothing to check now ends in a command; `status` names one for an unreadable stack; wording says "folder" or "instance".
- CI (`tests` job, ubuntu py3.13): the wheel must equal the tracked stack files minus READMEs; an instance from the installed wheel (scratch `HOME`) is made, checked, refused a second `init` (exit 3), given `config set stacks`; the three docker commands `init` prints start the demo. Job names `secrets` and `checks` unchanged. Not yet run on GitHub.
- Package version is now `0.2.0` (owner, from `0.1.0.dev0`); no tag exists.
- Measured (laptop, medians of 15, back to back against `f1ed535`): no start-up change beyond 1 ms (`--version` 15.7 and 16.2 ms before, 16.3 and 16.2 after). Timed run, scratch `HOME`, Colima started and stopped: wheel in hand to a hello that answers 7.0 s (uv) and 8.9 s (venv and pip) with `busybox:1.37.0` already cached (pull time not included; Colima start 16 s not included).
- Upgrade design rehearsed on a throwaway instance (scratchpad script, no repo code), 23 of 23 checks: three-way hash compare, edited plus changed upstream refused with the file named, staged tree plus two renames, rollback byte for byte, recovery after a crash between the renames. It found three rules the design needs: strip user-owned files from the kept `previous/` tree (a second copy of every `.env`), carry them back on rollback, delete `staging/` on recovery.

**Doc changes and reasons**
- `README.md`: two quick starts (runner path, fork path), `init` and `config` in the command list, how the folder is found. The runner path says the manual `docker compose` lines will be replaced by `nexahome up` and that overrides are not read by them (`-f` skips `compose.override.yaml`). A test keeps the lines equal to what `init` prints.
- `CONTRIBUTING.md`: package map and the one-way dependency rule. `docs/project.md`: current status names `init` and `config` (no register row touched). `tests/test_docs.py`: `nexahome init` left the planned list; `nexahome up` joined it (PK7).
- This log and `docs/roadmap.md`: PK6 done, Git list refreshed. No ADR edited, no row promoted.

**Deviations** (details in the local packaging README): the wheel already carried `.env.example` (a doubt in the plan was false); doctor warns, not fails, outside `$HOME` (master 4.5 says fails); plain path instead of `importlib.resources` (26.5 ms import); manifest written now although ADR 0020 puts it at stage 3; two test files landed in the `stacks/ release/` commit; the personal-data hook blocked two commits on false positives (renamed). Not run: Linux container leg, cold-image timing, uv fetching Python 3.13.

**Not verified:** every new CI step on GitHub; Python 3.13 on a runner; macOS and arm64 behaviour of the steps; a wheel from a published release; backup-first, a stateful image change and running containers during an upgrade swap; the hook with the package missing from `.venv`; the Mac mini, Linux hosts, Jetson, WSL2.

**Next:** (1) read the CI run on the pull request into `dev`, then merge decisions (yours); (2) the audit session you asked for: full code package and `stacks/` audit, every doc checked against the repo, docs compacted with this log first (prompt handed over); (3) PK7 to PK10 wait for B2. **Open questions:** the first tag: ADR 0020 and the register say `v0.1.0`, the package is `0.2.0`; overrides: ADR 0020 and master 4.3 promise `compose.override.yaml`, the manual commands cannot read it; ADR 0020's manifest timing; doctor severity for a mount outside `$HOME`.

**Pending:** superseded by the single list at the top of this log (2026-11-03, PK6).

## 2026-11-03: PK5 (hooks and `make check` use the package, old checks deleted, stacks bundled)

**Done**
- Step 0 as approved: the two uncommitted doc edits committed, `git fetch`, `git merge --no-ff origin/dev` (no conflict; `git diff origin/dev HEAD` showed only the doc commit's files); `make check` green before and after. Entry checks: no pull request is open; `main` requires `checks`, `secrets` and `gate` and its `ci.yml` has no `gate` job (the hang risk is latent, see Pending).
- Owner lifted the freeze rule for hooks and CI only. The four shell scripts were not changed: `setup.sh` installs the package so cannot call it, `deploy.sh` reaches the package through `make check`, `smoke.sh` and `backup.sh` have no package command yet (PK7 to PK9).
- `nexahome.policy.personal_data` gained `main` and a `__main__` entry; the pre-commit `personal-data` hook runs `python -m nexahome.policy.personal_data`. `make check` runs `nexahome check` instead of the script. "No stacks" and "Docker CLI missing" now exit 3 there (the script exited 0 and 1).
- The wheel carries `stacks/` as `nexahome/_stacks` and the sdist includes `/stacks`. A scratch probe showed hatch `force-include` ships a local `.env`, `data/` and every stack README (it ignores `.gitignore` and `exclude`), so `include` plus `[wheel.sources]` is used instead; that honours both. CI asserts every stack's `compose.yaml` is in the wheel and no `.env`, `data/` or README ships, then installs the wheel in a throwaway venv and runs `nexahome check --stacks` on the installed copy.
- `tests/test_docs.py`: headers against changelog dates, `Confirmed`/`Proposed` placement, relative links, documented `make` and `nexahome` commands, Dependabot coverage. It found no real drift. `Open` is not checked (ordinary verb); `nexahome init`, `make upgrade` and `make mini-check` are on a named allowlist (planned or cut).
- Parity gate, local: golden tests against the scripts, whole-tree hook output identical, `nexahome check` output identical. Then `scripts/check_compose.py` and `scripts/check_personal_data.py` were deleted in their own commit, and the golden tests now compare against recorded output (the personal-data fixture was recorded from the original script's real output).
- Measured (laptop, medians): personal-data hook 30.1 ms against 29.4 ms before (bare interpreter 22.7 ms); `nexahome check` 202 ms against 556 ms.

**Doc changes and reasons**
- `README.md`: the exit-code note and the `scripts/` line now describe the new state (the note said the hooks would switch in PK5).
- `CONTRIBUTING.md`: the repository-check bullet no longer says the hooks run the originals; it records why the wheel uses `include` and `sources`.
- `docs/constraints.md`, `docs/project.md` (Current status only): the Compose policy is run by `nexahome check`; the hook, `make check` and the wheel use the package. Header dates and changelog lines updated. No Confirmed row was edited.
- `docs/roadmap.md`: Next row, Packaging status and sessions, and a dated exception on the freeze-rule bullet (hooks and CI released on 2026-11-03 at the owner's request; ADR 0018's matching sentence is Proposed and was left unchanged). Reason: the bullet would otherwise contradict the work.

**Deviations from the plan**
- `force-include` was replaced (above). The first drafts of the docs tests were wrong twice (the local `CLAUDE.md` was scanned; `Open` matched as a label) and were narrowed.
- The preferred CI run before deletion did not happen: the owner held the push, so parity was proven locally only. Static names for the skipped platform jobs were not done (with a matrix a static name may make the legs indistinguishable; GitHub's behaviour not verified). `/session-end` was run by the owner, not the agent.

**Verification:** `make check` exit 0; `pytest` 322 passed on Python 3.14 and on 3.13.3 (scratch venv from the offline uv cache); working tree clean, nothing staged. The wheel steps were rehearsed against a scratch wheel (pass) and the assertion was shown to reject a `force-include` wheel. **Not verified:** the new CI steps on a GitHub runner with Python 3.13; macOS and arm64 behaviour of them; the hook with the package missing from `.venv`; docs-only skip, cancel-in-progress, `gate` failing on a failed job, platform jobs on a pull request into `main`, the weekly schedule (all unchanged from before); Dependabot with the anchors; a Dependabot pull request into `main`; the Mac mini, a Linux host, the Jetson, WSL2.

**Next:** (1) push `feat/packaging` and read the run on a pull request into `dev` (your yes); (2) PK6: `nexahome init`, instance layout, `nexahome.toml`, home resolution, README quick start, timed run (additive; the bundled stacks are in the wheel); (3) after PK6: the `dev` to `main` pull request.

**Open questions**
- Reword the ADR 0019 line that names the deleted script?
**Pending:** superseded by the single list at the top of this log (2026-11-03, PK5).

## Earlier entries, compacted (PK6c, 2026-11-03)

Entries before 2026-11-03 are summarised here; the full text is in git history (`git log -p -- docs/session-log.md`).

**2026-11-02, packaging track (branch `feat/packaging`):**
- *CI reshape.* Evidence from seven runs: Linux jobs waited 2 to 13 s, the macOS job waited about 300 s. Owner's answers: Linux amd64 only on every pull request into `dev`, a fast `gate` plus a non-required `platforms` summary, a weekly schedule plus manual runs, docs-only changes skip the code jobs. Pull request 22 merged later; ADR 0019 records the tiers.
- *PK4 close and PK4.* The `nexahome` package (`doctor`, `check`, `env`, `stacks`, `status`, `update`), standard library only, fully annotated; ported checks; `make test`; the `tests` CI job; pytest 9.1.1 and hatchling 1.32.4 approved (newest at least two weeks old); performance pass and audit (ADR 0021). Pushed on the owner's yes; pull request 22 into `dev`.
- *PK3.* `ci.yml` gained `portable` (Ubuntu amd64 and arm64, macOS arm64), SHA-pinned actions, ShellCheck, a `plan` job and `gate`; `setup.sh` stops early on Python older than 3.13. Green on pull request 21.
- *PK2.* Docs fixes F5 to F33 (live files), ADRs 0010 to 0012 promoted to Confirmed on the owner's explicit yes, runbooks got version headers, the branch `feat/p4-Atrack` deleted with `git branch -d`. `main` protection read back with `gh` (GET only).
- *PK1.* Read-only audit: 33 findings (3 high, 14 medium, 16 low), no broken links, every documented `make` target exists; ADRs 0014 to 0020 correctly Proposed.
- *PK0.* ADRs 0018 to 0020 written (Proposed); branch `feat/packaging` for the whole initiative; Linux arm64 runners are free for public repositories since August 2025; owner answers recorded in the plan.

**2026-11-02, P4 Track A (docs and one script):**
- *A3, ADR 0017.* Deploy flow: `make deploy` runs on the mini, anonymous HTTPS pull, a gitignored `.config/stacks` per host; `scripts/deploy.sh` (25 lines); the draft was audited against the repo and corrected (`git pull --ff-only` does not refuse on a non-overlapping dirty tree).
- *A2, ADR 0016.* Sleep, power, FileVault and updates; settings checked with `pmset` on the laptop; Wake-on-LAN, `caffeinate` and `disablesleep` rejected; owner: Ethernet, manual sleep only, restart after a power cut.
- *A1, SSH runbook and ADRs 0014 and 0015.* `docs/runbooks/mini-ssh.md`; ADR 0015 keys only, LAN only, no agent forwarding.

**2026-10-26:**
- *P4 planning.* Hardware plan for the Mac mini and the owned Jetson, shaped by four rounds of owner input; docs only.
- *P3 session 3.* Health widget removed from the portal tile, opt-in ntfy notifier (`NTFY_TOPIC` empty means off), S2 gaps verified.
- *P3 session 2.* `stacks/gatus` built (own Dockerfile, five targets at 30 s, 6.6 MiB idle, limit 32 MiB); edge alias and portal tile; ADR 0013 accepted.
- *P3 session 1.* Spike on Gatus and Uptime Kuma in throwaway projects, all removed afterwards; baseline memory figures; ADR 0013 drafted.

**2026-10-21 to 2026-10-23, P2.5 (user system, edge, portal, backups):**
- *Session 5.* Backup gap found and fixed (the job could not read the identity volume), `make verify`, `make backup-check`, `make snapshots`; restore drill passed; P2.5 closed.
- *Session 4.* `stacks/portal` (Homepage v2.6.0), the four-step contract, `make smoke`; 96 MiB anonymous, limit 256m.
- *Session 3.* Actual as the first OIDC client; sign-in matrix measured; `docs/runbooks/identity-recovery.md`.
- *Session 2.* `stacks/edge` (Caddy 2.11.7) and `stacks/identity` (Pocket ID v2.18.0); `make up` creates `nexahome-edge`.
- *Session 1.* Spike on Pocket ID, Caddy, Homepage and Actual: all arm64, non-root, read-only; decision recorded.
- *Planning (2026-10-21).* Two roles (admin, user), a later agent role that is never admin, provider first; the plan lives in the gitignored plans folder.

**2026-10-21, P2 (stack contract, backup, restore):**
- *P2 closed* after the owner's cold read of `docs/runbooks/restore.md`; owner actions closed (documentation version renamed 0.x).
- *Session 3, restore.* `make restore` never overwrites, uses `restic restore --verify`; drill on a fresh clone matched the fingerprint.
- *Session 2, backup.* ADR 0008 (restic 0.19.1, one-shot job), `stacks/backup`, `scripts/backup.sh`; spike leftovers removed.
- *Session 1.* `stacks/_template`, volume label and project name rules in the policy, Makefile with grouped help; Actual healthy on Colima.
- *Entry points.* Root README is the use entry, CONTRIBUTING the developer entry, `docs/README.md` start-here block.

**2026-10-20, foundation:**
- *Documentation foundation (version 1.0, now 0.x)*: project, constraints, observability, architecture, roadmap, runbooks.
- *Session 2, publish safely.* Full-history scan clean, public repository created (MIT), secret scanning and push protection on.
- *Session 1, pipeline proof.* Makefile, pinned tools, hooks (secrets, keys, large files, YAML, whitespace, no direct commits to `main` or `dev`, personal data), Colima 2 CPU, 2 GB, 20 GB (ADR 0004).
- *Session 0, bootstrap.* Git, `docs/`, ADRs 0001 to 0003, `/session-end` and `/adr` skills.
