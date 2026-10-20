# Documentation

Version 1.0 · Last reviewed 2026-10-20

Start with the [project overview](project.md). Each fact lives in exactly one document; every other document links to it.

## Index and ownership

| Document | Purpose | Owns |
| :--- | :--- | :--- |
| [project.md](project.md) | What NexaHome is and what it is not | Vision, scope, non-goals, audience, users, decision register, open questions |
| [constraints.md](constraints.md) | Rules every change must follow | Principles, frugality, Compose policy, tooling policy, security rules, agent guardrails |
| [architecture.md](architecture.md) | How the system is shaped and why | Layers, hosts, failure domains, trust zones, data and backup model, secrets and identity, remote access, migration paths |
| [observability.md](observability.md) | How we see what is running | Monitoring approach, decoupling rule, tool shortlist, inventory template |
| [roadmap.md](roadmap.md) | What gets built, in what order | Phases, sessions, hardware gates, now/next/later |
| [session-log.md](session-log.md) | What happened, newest first | History, CI status, pending owner actions |
| [adr/](adr/) | Why a decision was made | Decision rationale, one record per decision |

Reading order: project, constraints, architecture, observability, roadmap. The session log and ADRs are reference.

Other owners: how to contribute is in [CONTRIBUTING.md](../CONTRIBUTING.md), branching and branch protection are in [ADR 0002](adr/0002-branching.md), the container runtime in [ADR 0004](adr/0004-colima-runtime.md), the licence in [LICENSE](../LICENSE), and security reporting in [SECURITY.md](../SECURITY.md).

## Conventions

- Each file in `docs/` (except ADRs and the session log) has a header line under the title, `Version 1.0 · Last reviewed <date>`, and a one-line changelog as its last line. ADRs carry their own status and date; the root README and SECURITY.md follow the other conventions without a header.
- The labels Confirmed, Proposed and Open appear only in the decision register ([project.md](project.md)) and in ADRs. Elsewhere, prose says "decided" or "not decided yet" and links to the register.
- Filenames are lowercase kebab-case. Links are relative. A tracked file never links to a file that is not tracked.
- One H1 per file; headings in sentence case, not numbered.
- British English. State a fact once, then link to it.
- Nothing personal: no names, hostnames, IP addresses, emails or home paths.
- The documentation set is versioned as a whole: version 1.0 is the first complete, consistent set. Per-document history is the changelog line and git.

Changelog: 1.0 (2026-10-20): initial index and conventions.
