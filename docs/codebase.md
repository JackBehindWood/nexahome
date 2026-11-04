# Codebase

Version 0.1 · Last reviewed 2026-11-04

How the `nexahome` code is laid out, how to extend it and how to keep it fast. Setup and workflow are in [CONTRIBUTING](../CONTRIBUTING.md); the reasons for the language and layout are in the ADRs linked below.

## Layout

The code is in `src/nexahome/`, tests in `tests/` ([ADR 0018](adr/0018-code-package-and-language-strategy.md)). Standard library only; every function is annotated. Packages are split by concern, and dependencies point one way: `commands/` (thin) use the packages below, which never import `commands/` (a test checks it):

| Package | Holds |
| :-- | :-- |
| `docker/` | everything about the Docker CLI: `engine`, `compose`, the three Docker `doctor` probes, the shared network name. No other module writes a `docker` command line. |
| `instance/` | where an instance is (`home`), the stacks inside the package (`bundle`), what `init` does (`create`), `nexahome.toml` (`config`), the file hashes (`manifest`) |
| `stacks/` | which stacks exist and run (`catalogue`), who owns them (`ownership`), making and removing a user's own (`scaffold`), their `.env` files (`envfile`) |
| `release/` | the network and releases: `net` (the only module that may import a network module), `versions`, `updater` |
| `platform/`, `policy/` | what differs by operating system; the Compose and personal-data policy |
| top level | `cli`, `context`, `errors`, `runner`, `parallel`, `report`, `diagnosis`, `backup_info` |

## Extending it

- **A command:** one new thin module in `commands/`, named after the command, with `NAME` (the same as the file name), `register()` (name, help, options) and `run()`; it is found automatically (a module whose name starts with an underscore is a helper). Put the logic in a module outside `commands/` and import it inside `run()` (see `commands/doctor.py` and `diagnosis.py`). Raise `NexaHomeError(message, fix)` for a failure the user can fix: the fix is one exact command. The registry tests check `--help` and the Windows refusal for every command. Take everything from the `Context` (runner, environment, working directory, clock), so a test can replace it; logic that other commands will reuse goes into the package it belongs to (table above); call Docker through `docker.engine` and `docker.compose`, never write a `docker` command line elsewhere (`tests/test_packaging.py` checks it).
- **A `doctor` check:** a function `(ctx, prior) -> Check | None`, one `(id, function)` entry in `PROBES` in `diagnosis.py` (the Docker probes live in `docker/probes.py`), and a row in `tests/test_doctor.py`. A `warn` or `fail` needs a fix command; check ids are never renamed. Probes run side by side; reading `prior[...]` waits for that probe. The JSON schema is described once, in `nexahome/report.py`.
- **A system (macOS, Linux, ...):** a module in `platform/` and one line in `SYSTEMS`. Only `nexahome.platform` may read the operating system; a test enforces it.
- **A repository check:** `policy/` holds the Compose policy and personal-data checks. The pre-commit hook runs `python -m nexahome.policy.personal_data` and `make check` runs `nexahome check`; the scripts they replaced are gone, and the tests hold their recorded output. The wheel ships `stacks/` as `nexahome/_stacks` (plain `include` and `sources` in `pyproject.toml`, not `force-include`, which would also ship a local `.env`).

## Keeping the command fast

The principle is **pay for what you use**: a call costs only what it needs, in start-up time, memory, processes and network ([ADR 0021](adr/0021-command-line-performance.md) has the reasons, the measurements and what was considered). Checklist for every change:

1. **Import inside the function.** `json`, `hashlib`, `hmac`, `tempfile`, `secrets`, `shutil`, `shlex`, `urllib`, `ssl`, `http`, `concurrent`, `dataclasses`, `importlib.metadata`, the stdlib `platform` and `logging` are imported in the function that needs them. Type-only imports go under `if TYPE_CHECKING:`, and the module starts with `from __future__ import annotations` (3.13 evaluates annotations eagerly; 3.14 does not, so a local run on 3.14 alone hides the mistake).
2. **Keep `commands/` thin** and the logic outside it, so `nexahome --help` and every other command do not load it.
3. **No work at import time:** no I/O, no subprocess, no environment read when a module is imported.
4. **Run waiting calls side by side:** several independent `docker` calls go through `nexahome.parallel.map_ordered`; calls that may wait for an earlier result go through `nexahome.parallel.run_waiting`.
5. **Stream and cap:** a file or answer of unknown size is read in pieces and has a size limit; a directory is walked once.
6. **Use `NamedTuple` or a plain class for small records**, not `dataclass`.
7. **Measure before and after** and keep the number in the pull request: `python -X importtime -m nexahome <call> 2>&1 >/dev/null | sort -t'|' -k2 -n -r | head` for imports, `/usr/bin/time -l .venv/bin/python -m nexahome <call>` for peak memory (`-v` on Linux), the median of 15 runs for wall time.

`make test` enforces the checklist: `tests/test_startup.py` lists the modules each call imports in a fresh process, and `tests/test_packaging.py` rejects heavy top-level imports. If a new command truly needs a heavy module, add it to its own function and add the call to the budget in `test_startup.py`; add to the allowlist in `test_packaging.py` only with a reason next to the entry.

Changelog: 0.1 (2026-11-04): `stacks/` row names `ownership` and `scaffold` (Goal 3); 0.1 (2026-11-04): checklist names `run_waiting` (DR3); 0.1 (2026-11-03): moved here from CONTRIBUTING so the code guide has one owner (PK6f, owner's yes).
