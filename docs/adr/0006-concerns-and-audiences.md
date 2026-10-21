# 0006. Two entry points and an instance boundary

* **Status:** Proposed
* **Date:** 2026-10-21

## Context
Readers arrive with different goals: run NexaHome, change it, or understand it. Without clear entry points, setup steps for developers sit in front of people who only want to run a stack, and owner-specific data blurs into shared content.

## Decision
- The root README is the only entry for using NexaHome. The owner and an adopter follow the same commands with different data.
- CONTRIBUTING is the only entry for developing it (setup, checks, workflow). The owner as developer and a contributor follow the same rules.
- Using NexaHome never requires reading `docs/architecture.md`.
- Upstream is tracked content. An instance is a checkout plus untracked state: per-stack `.env`, data volumes, `.venv/`, `.personal-denylist`, `*.local.md`, and local agent and editor config. Outsiders never touch owner data.
- Makefile conventions, new layout directories, an update promise (release tags) and an operating entry are deferred: to P2 once built, and to the first release tag.

## Consequences
Refines, and does not change, the Confirmed audience and no-hosting rows and [ADR 0005](0005-agent-config-local.md). The README no longer carries developer setup. Deferred items are written down only when they exist.

## Alternatives
An `instance/` directory, a hosts file, a restructured `docs/` and a docs site add structure without a reader who needs it. `AGENTS.md` conflicts with ADR 0005. Issue templates, CODEOWNERS and a code of conduct wait for the first outside issue or pull request.
