# Session Log

Newest first. Each entry: done, doc changes with reasons, next, open questions.

## Pending owner actions (the one current list)

Last replaced 2026-11-03 (end of PK6f). Older entries end with a pointer here instead of their own list.

**Decide**
- Other Proposed register rows (documentation conventions, repository layout, task runner, security baseline, roles, three Packaging rows); review ADRs 0014 to 0020, the SSH runbook and the packaging design. None promoted in PK6f.
- The app-stack ADR draft (local, `.claude/tmp/`): your five answers are recorded in it; it becomes `docs/adr/0022-...` as Proposed once the first app is specified.
- GitHub: Dependabot alerts and security updates are disabled for the repository (your action, Settings, Code security); the account setting "Block command line pushes that expose my email"; optional SSH-signed commits.
- Open choices: digest pinning; paid tier versus the open-source rule; keep `hello` on the edge and in the portal; ruff or a type checker (answered: not now; revisit if a lint or typing bug slips through).
- Local `CLAUDE.md` still names `requirements-dev.txt` and CONTRIBUTING for the performance checklist (now `docs/codebase.md`): edit by hand.

**Git**
- Pull request 31 (`feat/packaging` into `dev`) is merged (2026-11-03, CI green on `b101a0f`). Next: `dev` into `main` by pull request (your yes).
- Dependabot (into `main`): 26 merged. 29 and 30 are green but wait until this branch reaches `main` (30 will conflict on the deleted `requirements-dev.txt`; 29 may on `pyproject.toml`; not verified). 25 and 27 await review (red `platforms` is the abandoned macOS leg); 28 (pocket-id) held.
- Optional: `nexahome init` smoke passed in a throwaway folder (init and check exit 0; doctor 3 only because no container runtime ran).

**Security hygiene**
- Keep `ENCRYPTION_KEY` and the restic password in a password manager (the repository is on the same disk: a drill, not protection); keep the ntfy topic secret.
- Confirm in Pocket ID that the first Actual client secret and the session 2 key `s2-config` are gone.
- A real second authenticator before real data exists; a permanent outsider test account and one Safari profile per test account ([test-sso](runbooks/test-sso.md)).
- Watch security alerts on GitHub for `pocket-id/pocket-id`, `caddyserver/caddy`, `gethomepage/homepage`, `TwiN/gatus`.

**Open work**
- Diagnose the Pocket ID self-restart; optional admin-only sign-in for the health view.
- Dependabot parsing is shown for `portal`, `identity`, `gatus` and `pip`; not yet for `github-actions`, `hello`, `actual`, `backup`, `edge`, `_template` (no newer tag is also a reason); the `dev` and `check` dependency groups are unproven until a Dependabot pull request appears after a push.
- Audit rows left for PK7 or later: S-21 (two `.env` creators until `nexahome up`), S-26 (backup job mounts every stack's `.env`), S-30 (deploy checkout and instance share a folder name), the package rows P-07 (trust model of `update`), P-11, P-12, P-14, P-16, P-18 to P-22, P-25 to P-27.

## 2026-11-03: PK6f session end

**Next:** `dev` into `main` by pull request on your yes, then PK7 after B2 (Mac mini) or earlier packaging work you choose; a possible small card to port the Makefile `.env` block (S-21). **Open questions:** the Pending list above. **Verified at the end:** `make check` exit 0; 442 tests pass (3.14 locally; CI also ran 3.13 on Linux, green); `tests/test_docs.py` 61 passed; nothing staged; tree clean after commits `7524289` and `b101a0f`, pushed. **Not verified:** CI on macOS and arm64 (skipped on a pull request into `dev`), Dependabot 29 and 30 conflicts against `main`, anything on hardware, the unexplained single 300 s timeout of the first full test run (reruns took 5 s).

## 2026-11-03: PK6f (decisions batch and pull request)

**Done**
- Pull request 31 opened `feat/packaging` into `dev` (not merged). CI on the 24 commits: `checks`, `secrets`, `plan`, `gate`, `hello up and down`, `portable (ubuntu-amd64)`, `tests` on Python 3.13 and 3.14 all passed; `platforms` and the macOS and arm64 legs were skipped on a pull request into `dev` by design.
- Dependabot: pull request 26 (busybox) merged into `main` with the owner's yes; 29, 30, 25, 27 and 28 stay open (29 and 30 wait until this branch reaches `main`; 30 will conflict on the deleted `requirements-dev.txt`).
- Owner answers: ADR 0022 draft recommendations accepted (kept local, copied to `docs/adr/` as Proposed only after the first app is specified); ruff not now (trigger: a lint or typing bug that slips through; a type checker waits for the same trigger); graphify leftovers dropped.
- `nexahome init` smoke in a throwaway folder outside the clone (removed afterwards): `init` exit 0, `check` exit 0, `doctor` exit 3 only because no container runtime was running (Colima not started, not started by this session).
- Code, at the owner's request after the doc work: `nexahome.parallel.run_waiting` (tasks that may wait for earlier ones; a `Mapping` of results, replacing `diagnosis._Prior` and its hand-rolled thread pool). `doctor` timing unchanged (median of 15: 137 ms before and after); 442 tests pass; `make check` exit 0. Uncommitted.
- Entry state differences from the prompt: 24 commits ahead of `origin/dev`, not 25.

**Doc changes and reasons** (owner ticked each item; no label changed)
- ADR 0007 line 13 (S-16, C1): `up`, `down` and `ps` follow `.config/stacks` when present (the Makefile has done so since ADR 0017). Line 14 (C2): `make upgrade` was cut. Line 14 (B2): "If ADR 0018 is decided, it supersedes this line in part."
- Register row Python tooling (B1): `pyproject.toml` exists now, link to ADR 0018.
- First tag `v0.2.0` in ADR 0020 and its register row (the package version; `update` would never offer `v0.1.0`).
- New `docs/codebase.md` (owner chose the name): the module map, "Extending it" and "Keeping the command fast" moved out of CONTRIBUTING (a move, so each fact keeps one owner); CONTRIBUTING keeps a pointer, `docs/README.md` has the index row and role-list link, ADR 0021 line 25 links the new anchor (owner's yes for that ADR edit; wording and label unchanged). Local `CLAUDE.md` still names CONTRIBUTING for the checklist (owner edits by hand).
- D1 needed no edit: "Ordered by the owner" was already removed in `46eac5a`.

## 2026-11-03: owner decisions after PK6e

**Done** (owner answers; all committed on `feat/packaging`, nothing pushed)
- Packaging-plan cleanup applied over the live local plan files (archives in `.claude/tmp/*-full.md`, `post-track-b-full.md` added).
- Commits: PK6d ADR wording, log and roadmap; graphify ignore files; lazy `subprocess` import in `runner.py` (blank line restored, 435 tests pass).
- Deleted `scripts/__pycache__` and the root `.env.example` (audit S-23; nothing reads it: stacks use their own, the Makefile and `nexahome` look under `stacks/<name>/`).

**Doc changes and reasons**
- ADR 0008 line 7: "register row Backup tool is Open" now says Confirmed (the register has said so since the drill; audit S-25). ADR 0009 line 12: ADR 0010 "Proposed" now "Confirmed 2026-11-02" (decided that day; audit S-25). Owner approved S-25; the Confirmed labels and decisions are unchanged.
- First tag decided as v0.2.0; the matching wording in ADR 0020 and the register row waits for the register batch with S-16 (owner: batch later).

**Open:** the other register rewords (B1, B2, C1, C2, D1, S-16); Dependabot merges and the push (owner chose "push only" when asked; not run yet); ADR 0022 draft; ruff or a type checker.

## 2026-11-03: PK6e (graphify trial, code pass only)

**Done**
- Entry state checked read-only. Differences from the prompt: graphify 0.9.46 was already installed (`uv tool`, global), so there was no install; `origin/feat/packaging` exists at the base commit 2605a93 (no PK6 commit pushed); the session log was 182 lines in the working tree (141 committed); `GEMINI_API_KEY` is set in the shell, so a document pass would have sent text to Gemini (not run).
- Owner approved an upgrade: 0.9.46 to 0.9.101 (`uv tool upgrade graphifyy`). Side effect: the first graphify run refreshed the global skill file (old copy kept as `.bak`); `~/.claude/CLAUDE.md` unchanged. A stray `src/graphify-out/` made by a read-only measurement was deleted.
- Code-only build, no model, 0 tokens: scratch copy first (99 files, 1,234 nodes, about 3 s), then the repo (142 files, 1,640 nodes, 3,292 edges, 113 communities, about 3 s); `graphify-out/` is gitignored; no `.claude/` or `.env` file is in the graph.
- Verdict: **not yet.** Q3 (what changes if `defaults.py` changes): 28 importers in 0.29 s, but it misses the function-level imports the repo uses on purpose (`cli.py`, ADR 0021) and a test string reference; grep found them in 0.03 s. Q2 (requirement IDs no test verifies): the graph has no ID nodes, a query returned about 6k tokens of noise; one `comm` line gave 19 IDs. Q1 (decision to code) needs documents: not run.
- Cost: 0 tokens, about 3 s per build, 159 MB of tool, 5 MB output. Removal: `uv tool uninstall graphifyy`, `graphify uninstall --purge`, delete `graphify-out/`.

**Doc changes and reasons**
- `.gitignore`: `graphify-out/` added (generated output must not be tracked; owner asked). New `.graphifyignore` (sensitive and local-only paths repeated so a `.gitignore` change cannot expose them; owner asked). Both are staged, not committed.
- Roadmap Next row, Done list and changelog; this entry and the Pending list. No ADR, register row or label changed in this session.

**Verified:** `make check` exit 0; `tests/test_docs.py` 59 passed; no `.env`, key, `data/` or `.claude/` staged. **Not verified:** the document pass, Q1, whether the Gemini key is free tier, token estimates, behaviour on Linux or the Mac mini, CI on any of this.

**Next:** your decisions (cleanup proposal, Dependabot order, push and pull request into `dev`, first tag, `scripts/__pycache__` and root `.env.example`, ADR 0022 draft, S-16 and S-25, commits, `runner.py` (it also dropped a blank line before `class RunResult`), ruff or a type checker). PK7 to PK10 after B2. A later graphify session only if Q1 is worth a probe.

**Open questions:** keep or revert the refreshed skill; track `.graphifyignore`; whether to allow a Gemini document pass.

## 2026-11-03: PK6d (app-stack ADR draft, packaging-plan cleanup)

**Done** (docs and local files only; no code written)
- Entry state checked read-only. Differences from the prompt: the PK6c session-end entry was uncommitted; the Dependabot pull requests all target `main` (30 is clean today and conflicts only after the chain reaches `main`; 29 may conflict on `pyproject.toml`); the local master plan has no sections 3, 5 or 9.
- A Proposed ADR draft for own images and application stacks, written to the gitignored `.claude/tmp/`, not to `docs/adr/`: adopt before build, a language-neutral contract (AS-1 to AS-13), runtime profiles (FastAPI and Streamlit first; Node, Go, Rust, C++, static, worker later; accelerators not covered), failure modes, evolution per hardware hop, a not-built list. Finding: a stack built with `build: .` would put its `.env` in the build context and `nexahome check` accepts it (scratch run, Docker CLI only), so the draft requires a `./app` context. Nothing promoted.
- A side-by-side cleanup of the local packaging plan: `audit.md` 389 to 108 lines (open rows, fixed rows with commits, decisions), README 127 to 92, cards 75 to 37, master and PK9 card extended for `nexahome clean`. Originals archived; live plan files not yet replaced.
- A plan for `nexahome clean [--all]` (dry run by default, refuses clones, `$HOME`, running containers; never touches backups or Docker volumes), recorded as PK-I5 and PK-I6 in the local plan and built in PK9. `~/.nexahome` does not exist; the owner meant `~/nexahome` and `.nexahome/`.

**Doc changes and reasons** (owner: "you are allowed to edit them if needed"; all Proposed ADRs, labels unchanged, uncommitted)
- ADR 0018: status line (stages 1 and 2 built, stage 3 partly, stage 4 not started), a sentence that hooks and CI were released on 2026-11-03, `force-include` replaced by `include` plus `sources`, and the "Go single binary" row now says it concerns the package (audit S-10; the code contradicted "no code exists").
- ADR 0019: the `tests` job description (wheel check, instance round trip, demo start) and the deleted macOS fallback sentence (`ci.yml` has no fallback).
- ADR 0020: status line, home resolution (`~/nexahome` only when it holds `nexahome.toml`), the manifest is written by `init`, `force-include` note.
- No Confirmed ADR, register row or label was changed. This log and the roadmap Next row and Done list were updated for the session.

**Verified:** `make check` exit 0; 435 tests pass on Python 3.14 (59 in `tests/test_docs.py`); nothing staged; no `.env`, key, `data/` or `.claude/` tracked; the draft's links resolve and its personal-data scan is clean. **Not verified:** anything on an engine (RAM, image size, health command, a build), CI on any of this, the Compose `pull_policy: build` wording against the official spec, Streamlit and Pocket ID group claims, Dependabot support for Conan and CMake, buildpacks on arm64, `docker init` under Colima, the #29 conflict, hardware.

**Next:** PK6e (graphify; ask before installing). Then your decisions below, and PK7 to PK10 after B2 (PK9 now carries `clean`).
**Open questions:** Go for app stacks (the draft recommends: owner-written Go is covered by "no Go"); template layout and sign-in for the first app; apply the cleanup proposal; which Confirmed-ADR edits to tick (S-16, S-25); first tag number; delete `scripts/__pycache__` and the root `.env.example`.
**Pending:** the list at the top.

## 2026-11-03: PK6c (audit fixes, docs compaction)

**Done** (19 commits on `feat/packaging`, `644839f` to `e92a46c`, not pushed; the prompt's rows were placeholders, so the audit's own recommendations were applied)
- Package: P-01, P-03, P-04, P-05, P-06, P-08, P-09, P-10, P-13, P-15, P-17, P-23, P-28, P-29, P-30 (two assertions). The Compose policy now enforces the hardening keys and reads `compose.override.yaml` (P-02, D-A, D-F); `check` supplies placeholders for required variables (D-K); `defaults.py` holds the shared limits and names (D1); `Context.checkout()` became `instance()` (D-C).
- Stacks and CI: template limits and Dependabot entry, gatus image name `nexahome/gatus:local` (D-G); `make check` covers untracked files (D-D); a deploy checkout installs the package, with a CI rehearsal step (D-E); `platforms` fails only on a failed leg (D-H).
- Tooling (D3, changed at the owner's request): `pyproject.toml` has a `check` group (pre-commit, pre-commit-hooks, detect-secrets) installed by `make setup`, and a `dev` group (pytest) installed only by `setup.sh --dev` or `make setup-dev`; `requirements-dev.txt` removed.
- Verified locally: `make check` green, 435 tests on Python 3.14.7 and 3.13.3, `tests/test_docs.py` 59 passed, start-up unchanged against `2605a93` (`--version` 28.7 ms both; the personal-data hook about 0.7 ms slower).

**Doc changes and reasons**
- Confirmed text, on the owner's per-item yes, no label changed: `docs/project.md` required checks now name `gate` and the health row names the opt-in ntfy notifier (both stale against GitHub and the stack); `docs/constraints.md` lists the enforced policy keys, all eight commands and the personal-data patterns; ADR 0003 and `constraints.md` name the `check` and `dev` groups.
- Proposed text, wording only: ADR 0019 (`gate` required since 2026-11-02, `nexahome check`), ADR 0014, ADR 0018 and register row 92 (plan wording instead of order and price detail), ADR 0018 line 20 (dependency group).
- Other: `docs/observability.md` (seven stacks, Gatus, ntfy), README (override and update notes), stack READMEs and comments (S-17 to S-19), `docs/project.md` package status, CONTRIBUTING (setup flow). This log compacted from 868 to 141 lines (older entries summarised, text in git history), Pending refreshed once, local-only actions moved to a gitignored note; roadmap Next row, Done list and stale status lines tidied. Your uncommitted session-end edits were kept and committed with the compaction.

**Next:** PK6d (app-stack ADR draft, doc only), then PK6e (graphify, ask before installing). Your decisions: merging Dependabot 26, 29, 30 (30 will conflict on the removed `requirements-dev.txt` and needs a Dependabot reopen), 25 and 27 after review, 28 held; a push of `feat/packaging`.
**Open questions:** first tag number (package 0.2.0, plan said `v0.1.0`); delete the root `.env.example` (S-23); delete `scripts/__pycache__`; the Proposed ADR wording batch (S-10); Go for app stacks.
**Not verified:** CI on any of this (including the deploy rehearsal step and the `platforms` change); `setup.sh --dev` end to end (the scratch rehearsal was refused; only `sh -n`, `make -n` and the earlier uv and pip rehearsals); Dependabot reading the dependency groups and the `_template` entry; macOS CI legs; engine, `make smoke` and all hardware.
**Pending:** the list at the top.

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
