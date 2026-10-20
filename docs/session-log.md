# Session Log

Newest first. Each entry: done, doc changes with reasons, next, open questions.

## 2026-10-20: Session 2, Publish safely

**Done**
- Pre-push checks: full-history scan found no personal terms, private IPs, home paths or secrets; detect-secrets clean on all tracked files; one author, the noreply identity; basic web search found no existing "NexaHome" project (not a trademark search).
- Merged `feat/session-1` into `dev` and `dev` into `main` (fast-forward, owner-approved), created the public repo `JackBehindWood/nexahome` (MIT), pushed `main` and `dev`.
- GitHub secret scanning and push protection are enabled (the default for public repos).
- The first push did not start a CI run, so the CI proof goes through a pull request from `feat/session-2` into `dev`.

**Open**
- Result of the first CI run and branch protection on `main`: see the entries added below as they complete.
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
