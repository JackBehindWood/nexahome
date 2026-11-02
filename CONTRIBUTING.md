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
make test                     # the package tests (pytest)
. .venv/bin/activate          # once per terminal: puts nexahome on your PATH (or call .venv/bin/nexahome)
nexahome --help               # the commands: check, doctor, env, stacks, status, update
nexahome doctor               # diagnose this machine (read-only)
```

Run `nexahome` from the checkout (or set `NEXAHOME_HOME` to it). The commands sit beside the Makefile, which stays the way to start and stop stacks; none of them starts a container. Exit codes are listed in the [README](README.md#the-nexahome-command). `update` is the only command that uses the network (`net.py`, https only); it asks before it installs and checks the wheel against `SHA256SUMS`.

To add a stack, follow [Add a stack](docs/runbooks/add-a-stack.md).

`make check` ends without errors when everything passes. To undo: `make unhooks`, delete `.venv`, and `colima delete` if you no longer need the runtime.

Agent and editor configuration (`CLAUDE.md`, `.claude/`, `.vscode/`) stays local and is never committed ([ADR 0005](docs/adr/0005-agent-config-local.md)); you need none of it.

## The nexahome package

The code is in `src/nexahome/`, tests in `tests/` ([ADR 0018](docs/adr/0018-code-package-and-language-strategy.md)). Standard library only; every function is annotated. To extend it:

- **A command:** one new thin module in `commands/`, named after the command, with `NAME` (the same as the file name), `register()` (name, help, options) and `run()`; it is found automatically (a module whose name starts with an underscore is a helper). Put the logic in a module outside `commands/` and import it inside `run()` (see `commands/doctor.py` and `diagnosis.py`). Raise `NexaHomeError(message, fix)` for a failure the user can fix: the fix is one exact command. The registry tests check `--help` and the Windows refusal for every command. Take everything from the `Context` (runner, environment, working directory, clock), so a test can replace it; logic that other commands will reuse goes outside `commands/` too (`envfile.py`, `stacks.py`, `docker.py`).
- **A `doctor` check:** a function `(ctx, prior) -> Check | None`, one `(id, function)` entry in `PROBES` in `diagnosis.py`, and a row in `tests/test_doctor.py`. A `warn` or `fail` needs a fix command; check ids are never renamed. Probes run side by side; reading `prior[...]` waits for that probe. The JSON schema is described once, in `nexahome/report.py`.
- **A system (macOS, Linux, ...):** a module in `platform/` and one line in `SYSTEMS`. Only `nexahome.platform` may read the operating system; a test enforces it.
- **A repository check:** `policy/` holds the Compose policy and personal-data checks. The hooks still run the originals in `scripts/` until PK5; the golden tests compare both.

### Keeping the command fast

The principle is **pay for what you use**: a call costs only what it needs, in start-up time, memory, processes and network ([ADR 0021](docs/adr/0021-command-line-performance.md) has the reasons, the measurements and what was considered). Checklist for every change:

1. **Import inside the function.** `json`, `hashlib`, `hmac`, `tempfile`, `secrets`, `shutil`, `shlex`, `urllib`, `ssl`, `http`, `concurrent`, `dataclasses`, `importlib.metadata`, the stdlib `platform` and `logging` are imported in the function that needs them. Type-only imports go under `if TYPE_CHECKING:`, and the module starts with `from __future__ import annotations` (3.13 evaluates annotations eagerly; 3.14 does not, so a local run on 3.14 alone hides the mistake).
2. **Keep `commands/` thin** and the logic outside it, so `nexahome --help` and every other command do not load it.
3. **No work at import time:** no I/O, no subprocess, no environment read when a module is imported.
4. **Run waiting calls side by side:** several independent `docker` calls go through `nexahome.parallel.map_ordered`.
5. **Stream and cap:** a file or answer of unknown size is read in pieces and has a size limit; a directory is walked once.
6. **Use `NamedTuple` or a plain class for small records**, not `dataclass`.
7. **Measure before and after** and keep the number in the pull request: `python -X importtime -m nexahome <call> 2>&1 >/dev/null | sort -t'|' -k2 -n -r | head` for imports, `/usr/bin/time -l .venv/bin/python -m nexahome <call>` for peak memory (`-v` on Linux), the median of 15 runs for wall time.

`make test` enforces the checklist: `tests/test_startup.py` lists the modules each call imports in a fresh process, and `tests/test_packaging.py` rejects heavy top-level imports. If a new command truly needs a heavy module, add it to its own function and add the call to the budget in `test_startup.py`; add to the allowlist in `test_packaging.py` only with a reason next to the entry.

## Workflow

1. Fork the repository and branch from `dev` (`feat/<topic>`).
2. Run `make check` before every push. It must pass.
3. Keep commits small and prefix them `docs:`, `feat:`, `fix:` or `chore:`.
4. Open a pull request into `dev`. CI (`secrets` and `checks`) must pass, and so should `gate`, which covers the Linux jobs; a change that only touches documentation skips the code jobs. A pull request into `main` also runs the macOS and arm64 jobs: read the `platforms` result before merging, because GitHub does not enforce it ([ADR 0019](docs/adr/0019-platform-support-and-ci-matrix.md)). Only the maintainer merges, and `main` takes pull requests only ([branching](docs/adr/0002-branching.md)).
5. Update the documentation with the change. Record a significant decision as an ADR in `docs/adr/`.

## Reporting security issues

Do not use issues. See [SECURITY.md](SECURITY.md).
