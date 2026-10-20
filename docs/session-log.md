# Session Log

Newest first. Each entry: done, doc changes with reasons, next, open questions.

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
