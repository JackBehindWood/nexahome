# 0018. Code package and language strategy

* **Status:** Proposed (design only; no code exists, so nothing here is proven)
* **Date:** 2026-11-02

## Context
Logic lives in shell and Python scripts (`scripts/backup.sh` 251 lines, `scripts/smoke.sh` 157, `scripts/deploy.sh`, `scripts/setup.sh`, two Python checks). They have no tests, CI runs only `make check`, and a newcomer must clone, install tools and read the Makefile. The roadmap deferred a code package until the same shell logic is copied into a third script ([P4 deferred items](../roadmap.md#p4-mac-mini-bootstrap)); [ADR 0007](0007-stack-contract.md) set a similar trigger for extracting shared Python. That trigger has not fired. The owner now wants the project portable and installable, which is a different reason, so this ADR says so and decides in stages that each stand alone.

Requirements and how each is verified:

| ID | Requirement | Verified by |
| :-- | :-- | :-- |
| PK-C1 | No runtime dependency beyond the standard library | Wheel metadata test |
| PK-C2 | One command, `nexahome`, stable exit codes (0 ok, 1 check failed, 2 usage, 3 environment not ready) and `--help` | Unit tests |
| PK-C3 | A ported command matches the shell original before the original is deleted | Golden tests against both, driven by a fake `docker` on `PATH` |
| PK-C4 | Type hints complete; every command has a failure-path test | Review, pytest |
| PK-P3 | Platform-specific code lives in one module, `platform.py` | Test: no other `sys.platform` or `uname` use |

## Decision
**Languages.** POSIX `sh` for glue only, small (about 30 lines), ShellCheck-clean in CI, no logic duplicated across scripts. Python **3.13 or newer** (owner's choice) for anything with logic: standard library only at runtime, `argparse` for the CLI. Build backend hatchling, build-time only. Dev tools: pytest, pinned in `requirements-dev.txt` per [ADR 0003](0003-project-local-tooling.md); each is still asked about before it is installed. Version policy: `requires-python >=3.13`; CI tests 3.13 and 3.14; a version is dropped at end of life with a changelog note.

**Stages, each a stop point.** Stopping after any stage leaves the repository coherent.
1. `nexahome doctor` and the test harness (fake `docker`). Additive; also useful alone.
2. Bundled stacks and `nexahome init`; the two Python checks move into the package ([ADR 0020](0020-instance-install-and-release-model.md)).
3. `upgrade` and the release pipeline.
4. Run-path ports (`up`, `backup`, `smoke`, `deploy`), **only after Track B step B2 has closed**. Until then no commit changes the run path that ADRs 0014 to 0017 are being tested on. Each old script stays until golden tests pass and is deleted in its own commit.

The Makefile stays as one-line shims, so documented `make` commands keep working. This amends by reference the Confirmed run-path rule in ADR 0007 ("Make and POSIX shell; Python for checks only") and the register row "no `pyproject.toml` until Python code needs it" (Python code now needs it, from stage 1). Neither is edited until the owner says yes.

## Consequences
Easier: tested logic, one install path, the same code on a laptop, the mini and CI, errors that end in a command. Harder: the first Python package and build step in the repository; a solo maintainer carries the package; Python 3.13 is newer than Ubuntu 24.04's 3.12, so non-uv users must supply it and the docs lead with uv. **Unverified:** that `uv tool install <wheel URL>` fetches Python 3.13 by itself (tested in stage 1); `make setup` on the macOS system Python 3.9.6; hatchling `force-include` for a directory tree.

Failure modes: wrong Python → pip refuses the wheel and `doctor` names the fix; Docker missing → stack commands stop with the start hint, `check` and `--version` still work; a port changes behaviour → old script kept until golden parity. Evolution: the CLI contract is the same on laptop, mini, Linux host and NAS; only environment variables change.

## Alternatives
| Option | Verdict |
| :-- | :-- |
| Keep shell and scripts, add tests with bats | Rejected: another tool, still no portable parsing or exit-code contract |
| click or typer | Rejected: runtime dependency |
| Go single binary | Rejected: owner does not know Go; maintenance risk |
| C++ helper | Not built. Trigger: a measured need Python misses; then a separate executable with a JSON contract, never an in-process extension |
| Python floor 3.11 or 3.12 | Not taken: owner chose 3.13; lowering later breaks nobody |
| ruff or a type checker now | Not proposed; added when a lint need shows up |
| Wait for the third-copy trigger | Not taken: portability and install are reasons the trigger did not cover |
