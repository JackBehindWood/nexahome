# Session Log

Newest first; each entry follows the template in the session-end skill and has at most 12 lines. Older entries are one line each under "Earlier entries"; the full text is in `git log -p -- docs/session-log.md`.

## Pending owner actions (the one current list)

Last replaced 2026-11-04 (end of the engine session). Entries end with a pointer here instead of their own list.

**Decide**
- Still open from DR2: register row 80 repeats row 81 (merge it or mark it historical); a runner guide and release notes after `v0.2.0`; the build for a runner's own stacks (`stacks.d/` or a Compose override, [ADR 0020](adr/0020-instance-install-and-release-model.md) and [0022](adr/0022-own-images-and-app-stacks.md)).
- `feat/packaging` carries the DR2 and DR3 commits (not pushed). Push and a pull request into `dev` on your yes; delete the branch only after it is merged.
- Other Proposed register rows (documentation conventions, repository layout, task runner, security baseline, roles, three Packaging rows); review ADRs 0014 to 0020, the SSH runbook and the packaging design. None promoted.
- [ADR 0022](adr/0022-own-images-and-app-stacks.md) (own images and application stacks) is Proposed: your five answers are recorded in it; promote only on your explicit yes. The ADR 0007 amendment (profiles) and ADR 0020's open gap wait for that.
- GitHub: Dependabot alerts and security updates are disabled for the repository (Settings, Code security); the account setting "Block command line pushes that expose my email"; optional SSH-signed commits.
- Open choices: digest pinning; paid tier versus the open-source rule; keep `hello` on the edge and in the portal; ruff or a type checker (not now; revisit if a lint or typing bug slips through).

**Git**
- Pull request 31 is merged into `dev` (2026-11-03). Next: `dev` into `main` by pull request (your yes).
- Dependabot (into `main`): 26 merged. 27 (Gatus v5.38.0) drilled and safe to merge: no migration, rollback by tag ([runbook](runbooks/dependabot-update.md)). 28 (Pocket ID v2.19.2) stays held on your call: it runs a one-way migration, so rollback is a restore, never the old tag. 29 and 30 are green but wait until this branch reaches `main` (30 will conflict on the deleted `requirements-dev.txt`; 29 may on `pyproject.toml`; not verified). 25 and 27 await review (red `platforms` is the abandoned macOS leg); 28 (pocket-id) held.

**Security hygiene**
- Keep `ENCRYPTION_KEY` and the restic password in a password manager (the repository is on the same disk: a drill, not protection); keep the ntfy topic secret.
- Confirm in Pocket ID that the first Actual client secret and the session 2 key `s2-config` are gone.
- A real second authenticator before real data exists; a permanent outsider test account and one Safari profile per test account ([test-sso](runbooks/test-sso.md)).
- Watch security alerts on GitHub for `pocket-id/pocket-id`, `caddyserver/caddy`, `gethomepage/homepage`, `TwiN/gatus`.

**Open work**
- Drill leftovers: Colima profile `drill` is stopped (`colima delete drill` frees its disk if you want it gone); the scratch copy is deleted. The Pocket ID self-restart is not diagnosed: the 45-minute watch was skipped at your request (0 restarts in the first 4 minutes only).
- Dependabot parsing is shown for `portal`, `identity`, `gatus` and `pip`; not yet for `github-actions`, `hello`, `actual`, `backup`, `edge`, `_template`; the `dev` and `check` dependency groups are unproven until a Dependabot pull request appears after a push.
- Audit rows left for PK7 or later: S-21, S-26, S-30 and package rows P-07, P-11, P-12, P-14, P-16, P-18 to P-22, P-25 to P-27 (local audit notes).

## 2026-11-04: engine drills (Gatus v5.38.0, Pocket ID v2.19.2, Dependabot runbook)

**Done**
- Gatus v5.37.0 to v5.38.0 on a throwaway Colima profile `drill` (your `default` profile untouched, still stopped): healthy, `make smoke` green, history kept (6 to 9 results), 7.0 MiB idle (6.8 before), 0 restarts; back to v5.37.0 healthy, history kept. No migration.
- Pocket ID v2.18.0 to v2.19.2: healthy, smoke green, issuer correct, cross-origin POST refused (403), 12 MiB idle (16 before). It runs migration `08-management.sql`; v2.18.0 then refuses the data ("downgrades are not allowed") and restart-loops. Rollback by `make restore` gave a fingerprint equal to the pre-bump one.
- New [Dependabot runbook](runbooks/dependabot-update.md); Goal 3 requirements and interface note written locally, nothing built.
**Doc changes and why:** `docs/runbooks/dependabot-update.md` new and listed in `docs/README.md`; ADR 0013 row 6 and the roadmap P3 line now carry the drill evidence instead of "no newer tag" (your instruction; no label changed).
**Next:** the Goal 3 session (audit and own stacks); `dev` into `main` on your yes. **Open:** the Pocket ID self-restart (the 45-minute watch on v2.19.2 was skipped at the owner's request; 0 restarts in about 4 minutes only, so v2.19 is neither cleared nor blamed).
**Verified:** the drills above, with commands run. **Not verified:** the 45-minute restart watch (skipped), a passkey login (fresh instance), a same-origin POST (my guessed endpoint gave 404), Linux, the mini, `make check` and `tests/test_docs.py` (see the final message).

## 2026-11-04: DR3 (edit batch for the accepted DR2 findings)

**Done**
- Committed the DR2 Step 0 edits as they stood (`dbb37b5`), then the DR2 S batch, one-owner changes, ADR index and log redesign (`81e64f0`), then SECURITY.md scope and supported versions (`b6951ca`). Not pushed.
- Command list owned by the README, stack count by `docs/project.md`, changelog lines trimmed to 8 entries, the log compacted to the new template.
**Doc changes and why**
- `docs/project.md`: Confirmed audience row reworded for running as shipped and row 84 loses its stale clause (owner's yes; labels unchanged); Proposed rows 61, 62, 96, 97 reworded.
- README, `docs/README.md`, architecture, observability, codebase, constraints, roadmap, CONTRIBUTING: DR2 S items and the one-owner changes. `docs/architecture.md` keeps the heading "Remote access" because ADR 0015 links its anchor.
- New `docs/adr/README.md` and two tests (ADR index, log budget 220 warn and 300 fail). The local session-end skill has the new template, compaction step and CI rule.
**Next:** the engine session (Gatus v5.38 and Pocket ID v2.19.2 drills, Dependabot runbook; needs your yes to start Colima), then an audit of `src/nexahome`, `tests/`, `stacks/` and `scripts/` for regular users, including making their own stack from the command.
**Verified:** `make check` 0; `tests/test_docs.py` 65 passed (log 149 lines, under the 220 warning; the fail path shown in a scratch copy); 0 bad anchors; SECURITY.md read against the repo (private reporting enabled, anchor resolves) and given a scope line for `nexahome update` and a supported-versions section. **Not verified:** GitHub rendering, the timed runner path, engine, mini.

## 2026-11-04: DR2 (edit batch, audit of the other docs, log shape)

**Done:** DR1 answers applied (28 edits, labels unchanged); `/docs-audit` over README, CONTRIBUTING and `docs/*.md`; log measurements and design (local `.claude/tmp/dr2-report.md`).
**Doc changes and why**
- Confirmed ADRs 0011, 0013, 0021: dead `check_compose.py` name, `[CONTRIBUTING]` label, `diagnosis.py` pool (clerical, owner's yes). ADR 0009 and its register row: Actual is the permanent reference client.
- Proposed ADRs 0014, 0016 to 0019: macOS 27, `nexahome check`, past-tense Context, the `uv` contradiction, a dated CI results line in 0019. ADR 0020 and 0022: direction for a runner's own stacks, not decided. ADR 0022 trimmed to two Python profiles.
- `docs/architecture.md`: general design versus reference deployment, host sizing rule moved from ADR 0014.
**Next:** DR3. **Open:** the session-end CI rule against the ADR 0019 line (resolved in DR3).
**Verified:** `make check` 0, `tests/test_docs.py` 62 passed, 0 bad anchors. **Not verified:** the timed runner path, engine steps, the mini.

## 2026-11-04: DR1 (audit of ADRs and runbooks, read-only)

**Done:** `/docs-audit` over 23 ADRs and 5 runbooks (local `.claude/tmp/dr1-report.md`). About 45 findings, no broken link or wrong label.
**Main findings:** stale facts in Proposed ADRs (macOS 27 reported, `check_compose.py` named after PK5, ADR 0018 Context in the past tense, a fused bullet in ADR 0019, `PK-P3` defined twice); the same in Confirmed 0011, 0013, 0021 (report only); ADR 0013's "no newer Gatus tag" out of date (v5.38.0); ADR 0022 over-built; no Dependabot runbook; `add-a-stack.md` assumes a clone.
**Doc changes and why:** none to ADRs or runbooks (read-first session). Owner goal recorded in local memory: NexaHome usable by others, the Mac mini the reference deployment.
**Next:** your answers, then DR2. **Verified:** `make check` 0, `tests/test_docs.py` 62 passed, `make -n` of 12 runbook targets. **Not verified:** engine-dependent runbook commands (Colima not started), anything on the mini, Pocket ID v2.19 and Gatus v5.38 behaviour.

## 2026-11-04: Housekeeping and ADR 0022 live

**Done:** [ADR 0022](adr/0022-own-images-and-app-stacks.md) moved from the local draft to `docs/adr/` as Proposed at the owner's request. Local-only: agent config, memory, plan indexes and `CLAUDE.md` refreshed; graph refreshed; `main` and `dev` level with `origin`.
**Doc changes and why:** ADR 0022 added; register row added in `docs/project.md`; [ADR 0018](adr/0018-code-package-and-language-strategy.md) line 40 points at ADR 0022. ADRs 0007 and 0020 not edited.
**Next:** the two documentation review sessions. **Not verified:** CI on this change (not pushed), the ADR's engine claims (it says so itself).

## 2026-11-03: PK6f (decisions batch, pull request 31, session end)

**Done**
- Pull request 31 (`feat/packaging` into `dev`) merged; CI on the 24 commits green except the macOS and arm64 legs, skipped by design on a pull request into `dev`. Dependabot 26 merged; 25, 27 to 30 stay open.
- Owner answers: ADR 0022 draft accepted; ruff not now; graphify leftovers dropped. `nexahome init` smoke in a throwaway folder passed.
- Code: `nexahome.parallel.run_waiting` replaced `diagnosis._Prior` (`doctor` median 137 ms before and after; 442 tests pass).
**Doc changes and why** (owner ticked each item; no label changed): ADR 0007 lines 13 and 14 (S-16, C1, C2, B2); register row Python tooling and first tag `v0.2.0`; new `docs/codebase.md` (a move from CONTRIBUTING, one owner per fact); ADR 0021 line 25 link.
**Next:** `dev` into `main` by pull request. **Verified:** `make check` 0; 442 tests; `tests/test_docs.py` 61 passed. **Not verified:** CI on macOS and arm64, Dependabot 29 and 30 conflicts, hardware, one unexplained 300 s timeout in a first full test run (reruns took 5 s).

## 2026-11-03: owner decisions after PK6e

**Done:** plan cleanup applied to the local packaging plan; commits for PK6d wording, graphify ignore files and a lazy `subprocess` import in `runner.py` (435 tests pass); deleted `scripts/__pycache__` and the root `.env.example` (nothing read it).
**Doc changes and why:** ADR 0008 line 7 and ADR 0009 line 12 stale status wording fixed (audit S-25; owner approved; labels unchanged). First tag decided as `v0.2.0`; the matching wording waited for the register batch.
**Open:** the other register rewords, Dependabot merges and the push (all resolved in PK6f).

## 2026-11-03: PK6e (graphify trial, code pass only)

**Done:** graphify upgraded 0.9.46 to 0.9.101 (owner's yes); code-only build, no model, 0 tokens: 142 files, 1,640 nodes, about 3 s; `graphify-out/` gitignored; no `.claude/` or `.env` file in the graph.
**Verdict: not yet.** It misses the function-level imports the repo uses on purpose (grep found them in 0.03 s) and has no requirement-ID nodes; the decision-to-code question needs a document pass (not run: `GEMINI_API_KEY` is set, so text would leave the machine).
**Cost:** about 159 MB of tool, 5 MB output. Removal: `uv tool uninstall graphifyy`, `graphify uninstall --purge`, delete `graphify-out/`.
**Doc changes and why:** `.gitignore` gains `graphify-out/`; new `.graphifyignore` repeating the sensitive paths. No ADR, row or label changed.
**Verified:** `make check` 0, `tests/test_docs.py` 59 passed. **Not verified:** the document pass, behaviour on Linux or the mini.

## 2026-11-03: PK6d (app-stack ADR draft, packaging-plan cleanup)

**Done** (docs and local files only)
- A Proposed ADR draft for own images and app stacks written to the gitignored `.claude/tmp/` (adopt before build, a language-neutral contract, runtime profiles, failure modes). Finding: a stack built with `build: .` would put its `.env` in the build context and `nexahome check` accepts it, so the draft requires a `./app` context.
- The local packaging plan cleaned (audit 389 to 108 lines); `nexahome clean` planned for PK9.
**Doc changes and why:** wording only in Proposed ADRs 0018, 0019, 0020 (status lines, `include` plus `sources`, home resolution, the `tests` job); no Confirmed ADR, row or label changed.
**Next:** PK6e. **Verified:** `make check` 0; 435 tests. **Not verified:** anything on an engine, CI on this, hardware.

## Earlier entries

One line each; the full text is in git history.

- **2026-11-03, PK6c (audit fixes, docs compaction):** 19 commits of package, stack, CI and tooling fixes (`defaults.py`, `check` and `dev` dependency groups, policy enforces the hardening keys); this log compacted from 868 to 141 lines.
- **2026-11-03, audit planning and Step 0:** read-only checks (383 tests, wheel contents, `main` already had `gate`); `feat/packaging` fast-forwarded to `origin/dev`; audit sessions PK6a to PK6e planned.
- **2026-11-03, PK6 (`init`, `config`, packages by concern):** `nexahome init` and `config`, packages `docker/` `instance/` `stacks/` `release/`, CI instance round trip, version 0.2.0; timed run 7.0 s with uv; upgrade design rehearsed 23 of 23.
- **2026-11-03, PK5 (hooks and `make check` use the package):** old check scripts deleted after a parity gate, stacks bundled in the wheel (`include` plus `sources`, not `force-include`), `tests/test_docs.py` added; freeze rule released for hooks and CI.

### Before 2026-11-03 (compacted in PK6c)

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
