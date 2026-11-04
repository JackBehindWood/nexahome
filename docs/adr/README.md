# Architecture decision records

One record per decision: why it was made, what was rejected, what it costs. Status (decided, proposed, open) is kept only in the [decision register](../project.md#decision-register), so it is not repeated here. Start a new record from the [template](0000-template.md); every file in this folder must have a row below (`tests/test_docs.py` checks it).

| ADR | Title | In one line |
| :-- | :-- | :-- |
| [0000](0000-template.md) | Template | The sections every record has |
| [0001](0001-docker-compose.md) | Docker Compose as the container orchestrator | Compose is the simplest tool that works; Kubernetes is out of scope |
| [0002](0002-branching.md) | Branching model | `main`, `dev` and `feat/<topic>`; merges into `main` only by pull request |
| [0003](0003-project-local-tooling.md) | Project-local tooling and opt-in git hooks | Tools live in `.venv`; no global installs; hooks are opt-in |
| [0004](0004-colima-runtime.md) | Colima as the laptop container runtime | A light, open-source Docker runtime for macOS |
| [0005](0005-agent-config-local.md) | Agent configuration stays local | `CLAUDE.md`, `.claude/` and `.vscode/` are never committed |
| [0006](0006-concerns-and-audiences.md) | Two entry points and an instance boundary | README to use, CONTRIBUTING to develop; owner data stays untracked |
| [0007](0007-stack-contract.md) | Stack contract | Template, volume label, project name and placeholders every stack follows |
| [0008](0008-backup-tool.md) | Backup tool: restic in a one-shot container | Encrypted, deduplicated backups without a resident service |
| [0009](0009-first-app-actual-budget.md) | First application: Actual Budget | Real SQLite data for the restore drill; the permanent reference client |
| [0010](0010-identity-provider.md) | Identity provider: Pocket ID | One small OIDC provider, two roles, agents never admin |
| [0011](0011-edge-and-local-hostnames.md) | Edge, local hostnames and shared network | Caddy and local names so browser and containers see one issuer |
| [0012](0012-portal.md) | Portal: Homepage as an open status board | A read-only launchpad without the Docker socket |
| [0013](0013-health-view.md) | Health view: Gatus | Config-as-code health history and an opt-in notifier |
| [0014](0014-mac-mini-hardware.md) | Mac mini hardware choice | The reference host's sizing and buy-when plan |
| [0015](0015-remote-access.md) | Remote access to the Mac mini | Key-only SSH on the LAN; VPN only when a need appears |
| [0016](0016-mac-mini-power-and-updates.md) | Mac mini sleep, power, FileVault and updates | Power and update policy for desk use |
| [0017](0017-deploy-flow.md) | Deploy flow to the Mac mini | `make deploy` in a deploy-only checkout with a per-host stack list |
| [0018](0018-code-package-and-language-strategy.md) | Code package and language strategy | Shell glue plus a tested Python package on the standard library |
| [0019](0019-platform-support-and-ci-matrix.md) | Platform support and CI matrix | macOS and Linux with evidence from tiered CI jobs |
| [0020](0020-instance-install-and-release-model.md) | Instance, install and release model | `nexahome init`, package-owned stacks, release wheels |
| [0021](0021-command-line-performance.md) | Command-line performance: pay for what you use | A call costs only what it needs; tests enforce it |
| [0022](0022-own-images-and-app-stacks.md) | Own images and application stacks | Adopt before build; a language-neutral contract for app stacks |
