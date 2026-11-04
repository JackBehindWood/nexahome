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
make setup     # create .venv with the nexahome package and the pinned check tools
make check     # hooks on every file plus the Compose policy check
make hooks     # optional: install the git pre-commit hook in this repo only
```

`make setup-dev` adds pytest, which only running the package tests needs (the `nexahome` package itself is installed by `make setup`, editable):

```sh
make setup-dev                # once: pytest
make test                     # the package tests (pytest)
. .venv/bin/activate          # once per terminal: puts nexahome on your PATH (or call .venv/bin/nexahome)
nexahome --help               # every command and option; the README describes them
nexahome doctor               # diagnose this machine (read-only)
```

Run `nexahome` from the checkout (or give `--home DIR`, or set `NEXAHOME_HOME`); the same lookup finds an instance made by `nexahome init`, which has no Makefile. The commands sit beside the Makefile, which stays the way to start and stop stacks; none of them starts a container. Exit codes are listed in the [README](README.md#the-nexahome-command). `update` is the only command that uses the network (`net.py`, https only); it asks before it installs and checks the wheel against `SHA256SUMS`.

To add a stack, follow [Add a stack](docs/runbooks/add-a-stack.md).

`make check` ends without errors when everything passes. To undo: `make unhooks`, delete `.venv`, and `colima delete` if you no longer need the runtime.

Agent and editor configuration (`CLAUDE.md`, `.claude/`, `.vscode/`) stays local and is never committed ([ADR 0005](docs/adr/0005-agent-config-local.md)); you need none of it.

## The nexahome package

The code is in `src/nexahome/` and the tests in `tests/`. The module map, how to add a command, a `doctor` check, a system or a repository check, and the checklist for keeping the command fast are in [docs/codebase.md](docs/codebase.md).

## Workflow

1. Fork the repository and branch from `dev` (`feat/<topic>`).
2. Run `make check` before every push. It must pass.
3. Keep commits small and prefix them `docs:`, `feat:`, `fix:` or `chore:`.
4. Open a pull request into `dev`. CI (`secrets` and `checks`) must pass, and so should `gate`, which covers the Linux jobs; a change that only touches documentation skips the code jobs. A pull request into `main` also runs the macOS and arm64 jobs: read the `platforms` result before merging, because GitHub does not enforce it ([ADR 0019](docs/adr/0019-platform-support-and-ci-matrix.md)). Only the maintainer merges, and `main` takes pull requests only ([branching](docs/adr/0002-branching.md)).
5. Update the documentation with the change. Record a significant decision as an ADR in `docs/adr/`.

## Reporting security issues

Do not use issues. See [SECURITY.md](SECURITY.md).
