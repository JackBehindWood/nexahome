# NexaHome: Principles, Constraints & Security

## 1. Systems Engineering Principles

* **Modularity:**
  * Define single responsibilities per component with clear boundaries.
  * Separate application code, runtime configuration, secrets, and persistent data.
  * Ensure components are independently deployable, testable, and replaceable.
* **Reproducibility:**
  * Keep all infrastructure configuration and code under version control (Git).
  * Automate setup and deployment steps where practical.
  * Document prerequisites, configuration, upgrade steps, and recovery procedures. Avoid undocumented manual interventions.
* **Portability:**
  * Prefer platform-independent solutions; platform-specific parts must be unavoidable, isolated, and documented with the reason.
  * Avoid hardcoding environment-specific filesystems, paths, or hostnames.
  * Prefer standard protocols and documented APIs to minimize lock-in.
  * Account for differences between macOS (ARM64), Linux, and container runtimes.
* **Simplicity:**
  * Prefer the simplest workable design.
  * **Docker Compose** is the container orchestrator (confirmed).
  * Avoid premature adoption of Kubernetes, complex microservice patterns, or custom orchestration tools.
* **Reliability** (checkable per service):
  * Every service has a health check, a restart policy, and a pinned image tag.
  * Persistent storage is separate from disposable application containers.
  * Backups are application-aware and verified by test restoration. Until a NAS exists, restore drills use a local volume only.

---

## 2. Technology Preferences

> **Note:** Everything in this section except Docker Compose is a preference, to be evaluated against requirements rather than treated as a mandate.

* **Version Control:** Git
* **Containerization:** Docker Compose (account for macOS Docker running inside a Linux VM)
* **Documentation:** Markdown & Architecture Decision Records (ADRs)
* **Configuration:** YAML, `.env` files, and shell scripts
* **Remote Access & Admin:** SSH keys, Tailscale / WireGuard VPN
* **Protocols:** Standard REST and MQTT; others (gRPC, OpenID Connect/OAuth2) only if a requirement appears.

*Do not select a NAS OS, container orchestration platform, or enterprise identity provider (IdP) until explicit requirements demand it. Configuration management (e.g. Ansible) is deferred until there is more than one host.*

---

## 3. Security Guidelines

* **Least Privilege:** Apply least privilege to users, system accounts, and AI agents.
* **Secrets Management:** **Never** commit passwords, API keys, private SSH keys, or live databases to Git.
* **Public repository:** Nothing personal is committed (names, institutions, hostnames, IPs, emails, home paths). Every stack ships a `.env.example` with placeholders; real `.env` files are gitignored. Secret scanning runs locally (opt-in hook) and in CI.
* **Network Exposure:** Keep administrative interfaces off the public internet; restrict to the local network or VPN. Published container ports bind to `127.0.0.1` by default.
* **AI Agent Guardrails:** AI agents **must not** receive unrestricted administrator root privileges by default. Destructive operations require explicit human approval.
* **Segmentation:** Plan for future network segmentation (e.g., placing IoT/ESP32 devices on an isolated VLAN).
* **Disaster Recovery:** Maintain a documented, manual administrator recovery path.

### Agent guardrails: enforcement

Status: **Proposed**, implemented in a local, uncommitted `.claude/settings.json`. Rules evaluate deny, then ask, then allow; the first match wins.

| Rule | Mechanism |
| :--- | :--- |
| Never commit secrets | Deny Read/Edit on `.env*` (except `.env.example`), key files, `secrets/`, `~/.ssh/`; scanners as backstop |
| No unrestricted root | Deny `sudo` |
| Destructive operations need approval | Deny `rm -rf`, force-push; ask before push, reset, clean, docker run/rm/up/down, brew, launchctl, system settings |
| Least privilege | Allow only a short list of read-only commands |

**Limits.** Command rules match the command text, so `/bin/rm`, `bash -c '...'`, or a script can slip past them. Read/Edit deny rules cover Claude's file tools and common file commands, not arbitrary programs. Secret scanning and the optional Claude Code sandbox are the backstops; the sandbox decision is open.
