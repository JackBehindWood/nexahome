# scripts

Shell glue that runs where the `nexahome` package cannot. The `Makefile` calls these; you normally run `make <target>`, not the script. Where new code goes, and why this folder only shrinks: [Script or package?](../docs/codebase.md#script-or-package).

| Script | Run by | What it does |
| :-- | :-- | :-- |
| `setup.sh` | `make setup`, `make setup-dev` | Checks `git`, `make` and Python, creates `.venv`, installs the package and the check tools. Runs before the package exists, so it stays shell. `--deploy <stack>...` prepares a deploy-only checkout ([ADR 0017](../docs/adr/0017-deploy-flow.md)). |
| `backup.sh` | `make backup-init`, `backup`, `restore`, `verify`, `snapshots`, `check`, `status` | The restic backup job around [`stacks/backup`](../stacks/backup/README.md). To be replaced by the package, then deleted. |
| `smoke.sh` | `make smoke` | Read-only checks of what is running; changes nothing. To be replaced by the package, then deleted. |
| `deploy.sh` | `make deploy` | Pull, check, start, on the host that runs the stacks. To be replaced by the package, then deleted. |

Rules for anything here: POSIX `sh`, ShellCheck-clean (CI runs it), about 30 lines, no JSON or TOML parsing, and a header that says why it cannot be Python. The package never calls a script. Tests: `tests/scripts/` runs `backup.sh` and `smoke.sh` unchanged against stub commands (no engine), and checks the Makefile's `.env` block against the package.
