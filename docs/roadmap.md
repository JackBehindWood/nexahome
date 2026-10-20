# Roadmap

Only the next session is detailed. Later sessions are outlines. Update via `/session-end`.

## Session 0: Bootstrap (done 2026-10-20)
- [x] Repository, docs moved to `docs/`, doc fixes, local agent config, decisions table, ADRs 0001-0003, license, README, SECURITY.md

## Session 1: Pipeline proof (done 2026-10-20)
- [x] Makefile, `.venv` (uv, pip fallback), pinned dev tools, opt-in hook installed, `.editorconfig`, `.gitattributes`
- [x] Colima runtime (ADR 0004), `stacks/hello`, compose policy check, lean CI file, PR template
- [x] Planted secret and personal data blocked by the hook; branch guard works; permission deny rules tested
- Not verified: CI (runs only after the first push, Session 2); that "ask" rules prompt (not observable from the agent side)

## Session 2: Publish safely (next)
**Goal:** push to a public GitHub repo with scanning and branch protection on.
- Merge `feat/session-1` into `dev` and `dev` into `main` (owner approval), name-collision check, history scan.
- Create the public repo, push `main` and `dev`, confirm CI is green.
- Enable secret scanning and push protection, protect `main` (no force-push or deletion, required checks).
- **Exit:** CI green on `main`; protections visible in repo settings; `git remote -v` shows only the new origin.
- **Verify:** `gh run list`, `gh api` on repo security settings and branch protection, `git log` review.
- Manual step for the owner: GitHub account setting "Block command line pushes that expose my email".

## Later (outline)
- **Session 3: Persistence and restore drill.** Named volume with a toy stateful service, backup script, runbook.
- **Session 4: Portal and health (optional).** Choose a lightweight dashboard or uptime tool via ADR.
- **Session 5: Mac mini bootstrap (needs hardware).** SSH from the MacBook Air (key-only, LAN and VPN, `~/.ssh/config` template with placeholders in a runbook), sleep policy, VPN decision, VS Code Remote-SSH, Claude Code on the mini (local `.claude/` and `CLAUDE.md` are not in git, so copy them by hand), deploy with `git pull && make check && make up`, rsync backups, local AI natively. No self-hosted GitHub runner on a public repo.
- **Session 6+: NAS, DNS, segmentation (needs hardware).**
- **First session with code:** add `pyproject.toml`, style tooling (ruff, clang-format, format-on-edit hook) and personal style rules.
