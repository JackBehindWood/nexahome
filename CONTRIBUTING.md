# Contributing

Pull requests are welcome. This is a solo hobby project with no support promise, and replies may be slow.

## Before you start

- Open an issue first for anything larger than a fix, so we agree on scope. Small fixes can go straight to a pull request.
- Read the [rules](docs/constraints.md) (Compose policy, tooling, security) and the [documentation conventions](docs/README.md#conventions).
- Nothing personal or secret in any commit: no names, hostnames, IP addresses, emails, home paths or credentials.

## Workflow

1. Fork the repository and branch from `dev` (`feat/<topic>`).
2. Run `make setup` once, then `make check` before every push. It must pass.
3. Keep commits small and prefix them `docs:`, `feat:`, `fix:` or `chore:`.
4. Open a pull request into `dev`. CI (`secrets` and `checks`) must pass. Only the maintainer merges, and `main` takes pull requests only ([branching](docs/adr/0002-branching.md)).
5. Update the documentation with the change. Record a significant decision as an ADR in `docs/adr/`.

## Reporting security issues

Do not use issues. See [SECURITY.md](SECURITY.md).
