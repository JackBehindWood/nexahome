# Contributing

Pull requests are welcome. This is a solo hobby project with no support promise, and replies may be slow.

## Before you start

- Open an issue first for anything larger than a fix, so we agree on scope. Small fixes can go straight to a pull request.
- Read the [rules](docs/constraints.md) (Compose policy, tooling, security) and the [documentation conventions](docs/README.md#conventions).
- Nothing personal or secret in any commit: no names, hostnames, IP addresses, emails, home paths or credentials.

## Developer setup

This is the only developer entry point ([ADR 0006](docs/adr/0006-concerns-and-audiences.md)); to just run a stack, use the [README](README.md).

Needs the README prerequisites plus Python 3.13 or newer, or `uv` (which fetches it); 3.13 is the project minimum. Without `uv`, `make setup` stops with the version it found if `python3` is older, so install `uv` or a newer Python first.

```sh
make setup     # create .venv and install the pinned dev tools
make check     # hooks on every file plus the Compose policy check
make hooks     # optional: install the git pre-commit hook in this repo only
```

`make setup` also installs the `nexahome` package (editable) and pytest:

```sh
.venv/bin/pytest              # the package tests
.venv/bin/nexahome doctor     # diagnose this machine (read-only)
```

To add a stack, follow [Add a stack](docs/runbooks/add-a-stack.md).

`make check` ends without errors when everything passes. To undo: `make unhooks`, delete `.venv`, and `colima delete` if you no longer need the runtime.

Agent and editor configuration (`CLAUDE.md`, `.claude/`, `.vscode/`) stays local and is never committed ([ADR 0005](docs/adr/0005-agent-config-local.md)); you need none of it.

## The nexahome package

The code is in `src/nexahome/`, tests in `tests/` ([ADR 0018](docs/adr/0018-code-package-and-language-strategy.md)). Standard library only; every function is annotated. To extend it:

- **A command:** a module in `commands/` with `NAME`, `register()` and `run()`, and one line in `COMMANDS` (`commands/__init__.py`). Raise `NexaHomeError(message, fix)` for a failure the user can fix: the fix is one exact command. The registry tests check `--help` and the Windows refusal for every command.
- **A `doctor` check:** a function `(ctx, prior) -> Check | None`, one `(id, function)` entry in `PROBES`, and a row in `tests/test_doctor.py`. A `warn` or `fail` needs a fix command; check ids are never renamed. The JSON schema is described once, in `nexahome/report.py`.
- **A system (macOS, Linux, ...):** a module in `platform/` and one line in `SYSTEMS`. Only `nexahome.platform` may read the operating system; a test enforces it.
- **A repository check:** `policy/` holds the Compose policy and personal-data checks. The hooks still run the originals in `scripts/` until PK5; the golden tests compare both.

## Workflow

1. Fork the repository and branch from `dev` (`feat/<topic>`).
2. Run `make check` before every push. It must pass.
3. Keep commits small and prefix them `docs:`, `feat:`, `fix:` or `chore:`.
4. Open a pull request into `dev`. CI (`secrets` and `checks`) must pass; the other jobs (`portable`, `tests`, `gate`) should too. Only the maintainer merges, and `main` takes pull requests only ([branching](docs/adr/0002-branching.md)).
5. Update the documentation with the change. Record a significant decision as an ADR in `docs/adr/`.

## Reporting security issues

Do not use issues. See [SECURITY.md](SECURITY.md).
