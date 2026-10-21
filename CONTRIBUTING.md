# Contributing

Pull requests are welcome. This is a solo hobby project with no support promise, and replies may be slow.

## Before you start

- Open an issue first for anything larger than a fix, so we agree on scope. Small fixes can go straight to a pull request.
- Read the [rules](docs/constraints.md) (Compose policy, tooling, security) and the [documentation conventions](docs/README.md#conventions).
- Nothing personal or secret in any commit: no names, hostnames, IP addresses, emails, home paths or credentials.

## Developer setup

This is the only developer entry point ([ADR 0006](docs/adr/0006-concerns-and-audiences.md)); to just run a stack, use the [README](README.md).

Needs the README prerequisites plus Python 3 (`uv` is optional).

```sh
make setup     # create .venv and install the pinned dev tools
make check     # hooks on every file plus the Compose policy check
make hooks     # optional: install the git pre-commit hook in this repo only
```

`make check` ends without errors when everything passes. To undo: `make unhooks`, delete `.venv`, and `colima delete` if you no longer need the runtime.

Agent and editor configuration (`CLAUDE.md`, `.claude/`, `.vscode/`) stays local and is never committed ([ADR 0005](docs/adr/0005-agent-config-local.md)); you need none of it.

## Workflow

1. Fork the repository and branch from `dev` (`feat/<topic>`).
2. Run `make check` before every push. It must pass.
3. Keep commits small and prefix them `docs:`, `feat:`, `fix:` or `chore:`.
4. Open a pull request into `dev`. CI (`secrets` and `checks`) must pass. Only the maintainer merges, and `main` takes pull requests only ([branching](docs/adr/0002-branching.md)).
5. Update the documentation with the change. Record a significant decision as an ADR in `docs/adr/`.

## Reporting security issues

Do not use issues. See [SECURITY.md](SECURITY.md).
