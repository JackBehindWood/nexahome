# 0021. Command-line performance: pay for what you use

* **Status:** Confirmed (the owner's design principle, confirmed on their explicit yes on 2026-11-02; the numbers below are measurements on one laptop, not a promise for other hosts)
* **Date:** 2026-11-02

## Context
The `nexahome` command ([ADR 0018](0018-code-package-and-language-strategy.md)) runs often and on small machines: a laptop that sleeps, a Mac mini at a desk, later a Jetson or a NAS. People call it for one small answer (`--version`, `doctor`, `stacks`). The owner's design principle for a Python command-line tool is **you pay for what you use**: a call costs only what that call needs, in time to first output, in memory, in imports, in processes started, in network and in disk. Nothing is loaded, read, started or fetched "in case".

The first build ignored this by default: `nexahome --version` took 46.7 ms against 12.6 ms for a bare `python -c pass`, because importing `cli` imported every command, which imported the network stack (`urllib`, `ssl`), `dataclasses` and more. `nexahome stacks` took 303 ms because it ran eight `docker compose ps` calls one after another.

## Requirements
Each has a check that fails when the rule is broken.

| ID | Requirement | Verified by |
| :-- | :-- | :-- |
| PK-F1 | `nexahome --version` imports no argparse, no command, no context: it costs the interpreter plus a few milliseconds | `tests/test_startup.py` (module list in a fresh process); timing recipe below |
| PK-F2 | A call imports its own command only. Commands are found from file names and loaded by name; help is the only call that loads all of them | `tests/test_startup.py`; `tests/test_registry.py` (names match modules) |
| PK-F3 | Heavy standard-library modules are imported inside the function that needs them, never at module level (allowlist in the test, each entry justified) | `tests/test_packaging.py::test_heavy_modules_are_imported_inside_functions` |
| PK-F4 | No work at import time: importing `nexahome` imports nothing; importing `nexahome.commands` loads no command; no I/O, subprocess or environment read happens before the command line is parsed | `tests/test_startup.py` |
| PK-F5 | Independent slow calls (a `docker` process each) run side by side, results in input order, bounded workers, threads only when there is more than one | `tests/test_parallel.py`, `tests/commands/test_stacks.py`, `tests/test_doctor.py` (order, errors); timing recipe |
| PK-F6 | Memory stays at the interpreter's own plus a few hundred KiB for every call; large data is streamed in fixed pieces, never held whole; every read from outside has a size limit | `/usr/bin/time -l` recipe; `tests/release/test_net.py::test_a_big_download_does_not_load_the_file_into_memory` (20 MiB file, under 2 MiB of Python memory) |
| PK-F7 | An optimisation needs a measurement before and after; a regression is caught by a test, not by memory | this ADR's table; the tests above |

## Decision
**Rules** (the how-to version for contributors is in [docs/codebase.md](../codebase.md#keeping-the-command-fast)):

1. **Import lazily.** A module imports at top level only what every use of that module needs. `json`, `subprocess` (outside `runner`), `hashlib`, `hmac`, `tempfile`, `secrets`, `shutil`, `shlex`, `urllib`, `ssl`, `http`, `concurrent`, `dataclasses`, `inspect`, `importlib.metadata`, the stdlib `platform` and `logging` go inside the function that uses them. Type-only imports go under `if TYPE_CHECKING:` with `from __future__ import annotations` (annotations that name such imports are evaluated eagerly on Python 3.13, which a test run on 3.14 hides).
2. **Commands are thin.** `commands/<name>.py` declares `NAME` (equal to the file name), the options (`register`) and `run`, and imports its logic inside `run`. The logic lives outside `commands/` (`diagnosis.py`, `updater.py`, `policy/`, `envfile.py`, ...). Help can then list every command without paying for any of them.
3. **Discover without importing.** Command names come from the file names in `commands/`; only the one named on the command line is imported.
4. **Fast paths for the cheapest calls.** `--version` is answered before argparse, the commands and the context exist.
5. **No work at import time, and no work nobody asked for.** The context (host facts, environment) is built after parsing. A probe that does not apply returns nothing and reads nothing. Files are read only by the command that needs them.
6. **Overlap waiting, not work.** Calls that wait on other processes (`docker`) run in threads through `nexahome/parallel.py` (and the doctor probes through `parallel.run_waiting`), at most 8 at a time, results in input order. No async framework, no process pool. The thread pool itself is imported only when there is more than one item.
7. **Stream, cap and stop early.** Downloads go to disk in 64 KiB pieces and are hashed on the way; every read from the network or a file has a size limit; directories are walked once, with constant memory.
8. **Plain data.** Small immutable records are `NamedTuple`s and the context is a plain class with `__slots__`, because `dataclasses` pulls in `inspect` (about 3.6 ms) for every call.
9. **Measure first, keep a number.** An optimisation is justified by a measurement. A saving under about 1 ms is not worth a less readable line.

**Budget.** `nexahome --version` within 5 ms of a bare interpreter (measured: 2.7 ms). A command's own start-up (imports and set-up before it does its work) aimed at 25 ms or less (a target, not yet measured per command); what a command waits for (`docker`, the network) is not part of that. Peak memory within 1 MiB of the bare interpreter for every call except `update` (network stack).

## Measurements
Laptop (Apple silicon), medians of 15 runs, start of process to exit, `python -m nexahome`; "before" is the first build; engine stopped except where noted.

| Call | Before | After, Python 3.14.7 | After, Python 3.13.3 |
| :-- | :-- | :-- | :-- |
| bare `python -c pass` | 12.6 ms | 12.6 ms | 17.4 ms |
| `nexahome --version` | 46.7 ms | **15.3 ms** | 20.2 ms |
| `nexahome --help` (loads every command's description) | 46.5 ms | 27.3 ms | 24.9 ms |
| `nexahome doctor` (three `docker` processes) | 105.9 ms | 79.6 ms | 76.3 ms |
| `nexahome stacks` (eight `docker compose ps`) | 303.4 ms | 111.9 ms | 109.4 ms |
| `nexahome check` against the original serial `scripts/check_compose.py` (eight `docker compose config`) | 322 ms | 123 ms | n/a |
| peak memory (`/usr/bin/time -l`), every call above | n/a | 16.9 to 17.0 MiB (bare interpreter 16.8 MiB) | n/a |
| `update` downloading a 20 MiB file | whole file in memory | under 2 MiB of Python memory | same |

Measured separately with `python -X importtime` (cumulative): `urllib.request` 7.3 ms (now only `update` pays), `dataclasses` 3.0 to 3.9 ms, `importlib.metadata` 2.1 ms, `typing` 1.1 ms. The other deferrals (`json`, `hashlib`, `tempfile`, `secrets`, `shutil`, `shlex`) were not measured one by one; each is one to a few milliseconds when unused.

**Recipe** (run from a checkout with `.venv`): `python -X importtime -m nexahome <call> 2>&1 >/dev/null | sort -t'|' -k2 -n -r | head`; peak memory: `/usr/bin/time -l .venv/bin/python -m nexahome <call>` (macOS; `-v` on Linux); wall time: median of 15 `subprocess.run` calls as in the session log.

## Considered and not done
| Idea | Why not now | Reconsider when |
| :-- | :-- | :-- |
| Replace argparse by a hand-written parser | On Python 3.14, building any parser costs about 40 modules and 7 to 9 ms (`argparse` imports `_colorize`, which imports `dataclasses` and `inspect`); on 3.13 it is cheap. A hand-written parser duplicates help text and error messages and is a maintenance cost | the budget cannot be met without it, or a call is run in a tight loop |
| Overriding argparse's private colour hook to skip `_colorize` | Private API; breaks silently across Python versions | argparse offers a public switch |
| `threading` instead of `concurrent.futures` | Saves about 2 ms of import (it pulls in `logging`) but adds hand-written concurrency code | `doctor` start-up is measured as the bottleneck |
| Long-running daemon, `zipapp`, PyInstaller, Nuitka, mypyc, Cython | Large complexity for a few milliseconds; ADR 0018 rejects compiled code until a measured need exists | a measured need that Python cannot meet (then a separate executable with a JSON contract, ADR 0018) |
| Talking to the Docker Engine socket instead of the `docker` CLI | Would remove the CLI's own start-up (measured: `docker --version` 9 ms, `docker compose version` 32 ms, one `docker compose config` 39 ms), but needs a hand-written client and the socket; Compose has no engine-side equivalent | `docker` process start-up dominates a call that runs often |
| Third-party lazy-import library | A runtime dependency (ADR 0018: none) | never needed while rule 1 is followed |
| Bytecode compilation at install | `pip` compiles at install; `uv` does not by default, and a missing `__pycache__` is written on first run when the directory is writable. Worth stating in the install docs (`uv tool install --compile-bytecode`) | PK9 writes the install instructions |

## Consequences
Easier: the common calls are close to a bare interpreter, the tool is pleasant on a small machine, and the budget is enforced mechanically. Harder: imports inside functions look unusual and a new contributor can undo the benefit without noticing, so the rules are in [docs/codebase.md](../codebase.md#keeping-the-command-fast) and checked by tests; `commands/` modules must stay thin, which separates the command-line shell from the logic (also a testing benefit). Failure modes: a heavy module imported at top level fails `test_packaging.py`; a command that imports another command's logic fails `test_startup.py`; a command whose `NAME` differs from its file name fails `test_registry.py`. Evolution: on a slower host (Jetson, NAS) the same rules matter more; the budget numbers above are laptop figures and will be re-measured on each hop, never assumed. If the Python version changes the interpreter's own start-up (3.14's argparse), the test allowlists name the exact cost.

## Alternatives
| Option | Verdict |
| :-- | :-- |
| Optimise only after a user complains | Rejected: the cost is cheapest to avoid while the structure is small |
| A lazy-import helper library | Rejected: dependency; plain function-level imports do the job |
| One big module per command for simplicity | Rejected: `--help` would load everything again |
| Keep everything eager and accept about 47 ms | Rejected by the owner's principle |
