# Documentation

Version 0.1 · Last reviewed 2026-11-04

Each fact lives in exactly one document; every other document links to it.

## Start here by role

Roles follow [ADR 0006](adr/0006-concerns-and-audiences.md), decided (see the register in [project.md](project.md)).

- **Run a stack:** the root [README](../README.md), which also lists the `nexahome` command. Nothing in `docs/` is required to start; read the [restore runbook](runbooks/restore.md) before you rely on a backup. To add a stack of your own: [Make your own stack](runbooks/own-stack.md).
- **Customise:** fork the repository, then follow the fork path in the [README](../README.md) and [Add a stack](runbooks/add-a-stack.md).
- **Change or contribute:** [CONTRIBUTING.md](../CONTRIBUTING.md), the [codebase guide](codebase.md) (layout, how to extend the `nexahome` package, keeping it fast), then [constraints](constraints.md). To add a stack: [runbook](runbooks/add-a-stack.md).
- **Understand the design:** [project](project.md), then [architecture](architecture.md).

## Index and ownership

| Document | Purpose | Audience | Owns |
| :--- | :--- | :--- | :--- |
| [project.md](project.md) | What NexaHome is and what it is not | All | Vision, scope, non-goals, audience, users, decision register, open questions |
| [codebase.md](codebase.md) | How the `nexahome` code is laid out, extended and kept fast | Developers | Package layout, extension checklists, performance checklist |
| [constraints.md](constraints.md) | Rules every change must follow | Developers | Principles, frugality, Compose policy, tooling policy, security rules, agent guardrails |
| [architecture.md](architecture.md) | How the system is shaped and why | Developers, operators | General design versus reference deployment, layers, hosts, failure domains, trust zones, data and backup model, secrets and identity, remote access, migration paths |
| [observability.md](observability.md) | How we see what is running | Operators | Monitoring approach, decoupling rule, tool shortlist, inventory template |
| [roadmap.md](roadmap.md) | What gets built, in what order | All | Phases, sessions, hardware gates, now/next/later |
| [session-log.md](session-log.md) | What happened, newest first | Maintainer | History, CI status, pending owner actions |
| [runbooks/](runbooks/add-a-stack.md) | Step-by-step how-tos, each opening with audience and admin need | Per runbook | Procedures (add a stack and what is stable for scripts and tools, [restore](runbooks/restore.md), [identity recovery](runbooks/identity-recovery.md), [test sign-in](runbooks/test-sso.md), [SSH to the mini](runbooks/mini-ssh.md), [update from a Dependabot pull request](runbooks/dependabot-update.md), [make your own stack](runbooks/own-stack.md)) |
| [adr/](adr/README.md) | Why a decision was made | Developers | Decision rationale, one record per decision; the index lists every ADR |

Reading order for the design: project, constraints, architecture, observability, roadmap. The session log and ADRs are reference.

Other owners: how to contribute is in [CONTRIBUTING.md](../CONTRIBUTING.md), entry points and the instance boundary are in [ADR 0006](adr/0006-concerns-and-audiences.md), branching and branch protection are in [ADR 0002](adr/0002-branching.md), the container runtime in [ADR 0004](adr/0004-colima-runtime.md), the licence in [LICENSE](../LICENSE), and security reporting in [SECURITY.md](../SECURITY.md).

## Conventions

- Each file in `docs/` (except ADRs and the session log) has a header line under the title, `Version 0.1 · Last reviewed <date>`, and a one-line changelog as its last line. ADRs carry their own status and date; the root README and SECURITY.md follow the other conventions without a header.
- The labels Confirmed, Proposed and Open appear only in the decision register ([project.md](project.md)) and in ADRs. Elsewhere, prose says "decided" or "not decided yet" and links to the register. The session log is exempt: it is a history and quotes the labels as they were when written.
- Filenames are lowercase kebab-case. Links are relative. A tracked file never links to a file that is not tracked.
- One H1 per file; headings in sentence case, not numbered.
- British English. State a fact once, then link to it.
- A changelog line keeps its newest 8 entries; older ones are in git. The session log stays under 300 lines (`tests/test_docs.py`): the newest 8 entries in full, older ones one line each.
- Nothing personal: no names, hostnames, IP addresses, emails or home paths.
- The documentation set is versioned as a whole: version 0.1 is the first complete, consistent set (1.0 is reserved for the first release tag). Per-document history is the changelog line and git.

Changelog: 0.1 (2026-11-04): add-a-stack gains the stable-interfaces section; 0.1 (2026-11-04): own-stack runbook listed (Goal 3); 0.1 (2026-11-04): Dependabot update runbook listed; 0.1 (2026-11-04): customise role, runner line, ADR index, changelog and log rules (DR3); 0.1 (2026-11-03): codebase guide added and linked, moved out of CONTRIBUTING (PK6f); 0.1 (2026-11-02): the `nexahome` command and package guide linked from the role list (PK4); 0.1 (2026-11-02): session log exempt from the label rule (PK2); 0.1 (2026-11-02): SSH runbook listed; 0.1 (2026-10-21): documentation version is 0.x until the first release tag; version renamed from 1.0; 0.1 (2026-10-21): restore runbook listed; 0.1 (2026-10-21): runbooks row, start-here block and audience column
