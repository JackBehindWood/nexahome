# Roadmap

Only the next session is detailed. Later sessions are outlines. Update via `/session-end`.

## Session 0: Bootstrap (done 2026-10-20)
- [x] Repository, docs moved to `docs/`, doc fixes, CLAUDE.md, `.claude/` (settings, `/session-end`, `/adr`)
- [x] `.gitignore`, `.env.example`, LICENSE, README, SECURITY.md, ADRs 0001-0003, roadmap, session log
- [x] Local commit on `main`; `dev` and `feat/session-1` created. No remote, nothing pushed.

## Session 1: Pipeline proof (next)
**Goal:** one trivial service running, with checks live.
- 1a: Makefile, `make setup` (`.venv`, pinned pre-commit and detect-secrets), opt-in `make hooks`/`make unhooks`, `.editorconfig`, `.gitattributes`, `.vscode/`. Explain every install and hook before running it.
- 1b: container runtime decision (ADR), `stacks/whoami` (pinned multi-arch image, healthcheck, `127.0.0.1` bind), local `.claude/rules/compose.md`, lean `.github/` CI, permission rule test, sandbox decision.
- **Exit:** `make up` healthy, `make down` clean, `make check` green, a planted fake secret blocked by hook and CI, every permission rule behaves as designed.
- **Verify:** `docker compose config`, `curl` the local port, `docker compose ps`, `make check`, `make unhooks`.

### Permission rule test (run in Session 1)
Observe deny / prompt / silent for: `sudo true`; `rm -rf` on a scratch path; `git push --force`; Read of a dummy `.env` (then delete it) and of `.env.example`; `docker ps`, `docker compose config`, `docker compose ps` (silent); `docker compose up`, `docker run` (prompt). In particular check that `Read(!.env.example)` carves out correctly.

## Later (outline)
- **Session 2: Publish safely.** GitHub secret scanning and push protection, branch protection, name-collision check, verify the noreply address, add remote only on explicit approval.
- **Session 3: Persistence and restore drill.** Named volume with a toy stateful service, backup script, runbook.
- **Session 4: Portal and health (optional).** Choose a lightweight dashboard or uptime tool via ADR.
- **Session 5: Mac mini bootstrap (needs hardware).** SSH from the MacBook Air (key-only, LAN and VPN, `~/.ssh/config` template with placeholders in a runbook), sleep policy, VPN decision, VS Code Remote-SSH, Claude Code on the mini, deploy with `git pull && make check && make up`, rsync backups, local AI natively. No self-hosted GitHub runner on a public repo.
- **Session 6+: NAS, DNS, segmentation (needs hardware).**
- **First session with code:** add style tooling (ruff, clang-format, format-on-edit hook) and personal style rules.
