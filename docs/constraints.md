# Principles, constraints and security

Version 0.1 · Last reviewed 2026-11-03

Rules every change must follow. Decisions and their status are in the [register](project.md#decision-register).

## Principles

Each principle has a check you can run or read.

| Principle | Rule | Check |
| :--- | :--- | :--- |
| Modularity | One responsibility per stack; code, configuration, secrets and data are separate | A stack is one directory under `stacks/` with `compose.yaml`, `.env.example` and a README |
| Reproducibility | Configuration lives in Git; setup and recovery steps are written down | A fresh clone plus `make setup` and `make check` works (see the [README](../README.md)) |
| Portability | Same files on macOS and Linux; platform-specific parts are isolated and explained | No hardcoded paths, hostnames, IPs or UIDs; paths come from environment variables |
| Simplicity | Prefer the simplest design that works today; Docker Compose only | No Kubernetes, custom orchestrator or "for later" abstraction without an ADR |
| Frugality | Affordable, energy efficient, low maintenance. Open-source software first; no paid subscriptions; no always-on workload unless it needs to be always on; complexity only when justified | New services state their RAM and disk need and whether they must run 24/7; nothing runs that is not used |
| Reliability | Every service has a health check, a restart policy and a pinned image; data survives container replacement | `nexahome check`; backups count only after a tested restore |

## Compose policy

Enforced by `make check` (`nexahome check`) unless marked review.

- Image pinned to an exact tag; never `latest`; multi-arch (arm64 and amd64), no amd64-only images (review).
- Health check and restart policy on every service. Exception: a one-shot job started by a script (the backup) carries the label `nexahome.oneshot: "true"` and is exempt from these two rules only; the image pin, port, privilege and network rules still apply ([ADR 0008](adr/0008-backup-tool.md)).
- Published ports bind to `127.0.0.1`, with the host port from an environment variable with a default.
- No `network_mode: host` and no `privileged`. No Docker socket mount (enforced). No `cap_add` except `NET_BIND_SERVICE` (Caddy's file capability, [ADR 0011](adr/0011-edge-and-local-hostnames.md)). The only external network is `nexahome-edge`, which `make up` creates; both enforced.
- Run as non-root, `cap_drop: [ALL]`, `no-new-privileges`, read-only root filesystem where possible (review).
- No inline secrets: values come from a gitignored `.env`; every variable is listed in `.env.example` with a placeholder.
- Persistent data uses a named volume or the gitignored `data/` directory, never a tracked path or the stack directory. Read-only static content that ships in the repository (as in `stacks/hello`) is not persistent data.
- Every named volume carries the label `nexahome.backup` with `"true"` or `"false"`; the project name is `nexahome-<directory>`. Both are enforced by `make check` ([ADR 0007](adr/0007-stack-contract.md)).
- A `.env` value of `CHANGE_ME` is a placeholder: `make up` stops until it is replaced. A value of `GENERATE` is replaced by a random value when `make up` first creates `.env`; it is never printed.
- New stacks start from `stacks/_template/` ([runbook](runbooks/add-a-stack.md)).

## Makefile conventions

- `make` with no target prints the help. Every target has a `## text` description and sits under `##@ Use` (for people running stacks) or `##@ Develop` (for contributors).
- Target names are bare lowercase verbs, with a hyphen for verb-noun. Variables are UPPERCASE (`STACK`); environment variables are `NEXAHOME_*` with defaults.
- `up`, `down` and `ps` act on every stack except `_template` and `backup` unless `STACK=name` is given. `down` never removes volumes.
- GNU make 3.81 syntax only (the version macOS ships), so no `$(file ...)` or `.ONESHELL`. One Makefile until it passes about 150 lines.
- `make smoke` is read-only (never starts or stops anything). The run path (`up`, `down`, `backup`, `restore`, `smoke`, `deploy`) is Make and POSIX shell for now. Python is used for the checks and for the `nexahome` command in `src/nexahome` (`doctor`, `check`, `env`, `stacks`, `status`, `update`), which sits beside the run path and starts no container. [ADR 0018](adr/0018-code-package-and-language-strategy.md) (drafted, not decided yet) proposes moving the run path into the package in stages, not before the Mac mini's Track B step B2 has closed. `make verify` refuses to run on a running stack and always removes its check copy. The one platform-specific line is `make open` (`open` on macOS, `xdg-open` elsewhere; not tested on Linux).

## Tooling policy

- Dev tools are pinned in `requirements-dev.txt` and installed into the gitignored `.venv` ([ADR 0003](adr/0003-project-local-tooling.md)).
- No global or Homebrew installs and no new git hooks without the owner's approval. The request states what the tool does, where it installs, whether it changes global configuration and how to remove it.
- The `nexahome` package follows the pay-for-what-you-use rules (lazy imports, thin commands, side-by-side waits, streamed and capped data; [ADR 0021](adr/0021-command-line-performance.md)); `make test` enforces them.
- Optional linters and security scanners are added when a concrete need appears. The pre-commit hook is installed only with opt-in (`make hooks`, removed by `make unhooks`).

## Security rules

- **Never commit:** passwords, API keys, tokens, private keys (SSH or TLS), live databases, `.env` files, and personal data (names, institutions, hostnames, IP addresses, emails, home paths). Use `.env.example` with placeholders. A committed secret is compromised: rotate it first, then report it ([SECURITY.md](../SECURITY.md)).
- **Scanning:** secrets and personal data are checked locally by the pre-commit hook and by CI.
- **Exposure:** administrative interfaces stay off the public internet; local network or VPN only.
- **Least privilege:** applies to users, service accounts and AI agents. No `sudo`, root containers or `--privileged` without the owner's explicit approval.
- **Destructive or system-changing actions** (delete, force-push, reset, container runtime, package manager, service manager, network or power settings) need the owner's approval.

## Agent guardrails

AI agents never receive unrestricted administrator rights, never read or write secrets, and need approval for destructive operations. They are enforced by local, uncommitted agent settings ([ADR 0005](adr/0005-agent-config-local.md)):

| Rule | Mechanism |
| :--- | :--- |
| No secrets | Deny reading and editing `.env*` (except `.env.example`), key files, `secrets/` and SSH keys; scanners as backstop |
| No unrestricted root | Deny `sudo` |
| Destructive operations need approval | Deny `rm -rf` and force-push; ask before push, reset, clean, container run/remove/up/down, package manager, service manager, system settings |
| Least privilege | Allow only a short list of read-only commands |

Rules evaluate deny, then ask, then allow; the first match wins. Limits: rules match the command text, so `bash -c '...'`, a different path to the same program, or a script can bypass them; file deny rules cover the agent's file tools and common file commands, not arbitrary programs. Secret scanning and the optional sandbox are the backstops. That the ask rules prompt for container commands has not been observed.

## Technology preferences

Preferences, not mandates; evaluate against requirements. Git, Markdown and ADRs, YAML and `.env` files, SSH keys for remote access, REST and MQTT as protocols. Not selected until a requirement appears: NAS operating system, orchestration platform, identity provider, configuration management (not before a second host).

Changelog: 0.1 (2026-11-03): Compose policy is run by `nexahome check` (PK5); 0.1 (2026-11-02): the nexahome command list names `env`, not `setup` (CI redesign session); 0.1 (2026-11-02): run-path line reworded for the nexahome package and the performance rule added, owner's yes (PK4); 0.1 (2026-11-02): language rule points at ADR 0018 (PK2 reword B3); 0.1 (2026-11-02): `NEXAHOME_DATA_DIR` claim removed, nothing reads it (PK2); 0.1 (2026-10-23): `make smoke`; 0.1 (2026-10-23): `make open` platform note; 0.1 (2026-10-22): `cap_add`, socket and external-network rules enforced; `GENERATE` placeholder; 0.1 (2026-10-21): version renamed from 1.0 (pre-release project); 0.1 (2026-10-21): one-shot job exception; 0.1 (2026-10-21): volume label, project name and placeholder rules, Makefile conventions; 0.1 (2026-10-20): frugality expanded; reorganised into principles, Compose policy, tooling, security and guardrails; frugality and tooling policy added; Compose policy moved here from local files; VPN and SSH method preferences removed (open in the register).
