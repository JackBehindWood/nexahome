# 0018. Code package and language strategy

* **Status:** Proposed (stages 1 and 2 are built and tested, stage 3 partly (manifest, `update`); stage 4 is not started; the design as a whole is not decided)
* **Date:** 2026-11-02

## Context
At the start of the track (2026-11-02) logic lived in shell and Python scripts (`scripts/backup.sh` 251 lines, `scripts/smoke.sh` 157, `scripts/deploy.sh`, `scripts/setup.sh`, two Python checks). They had no tests, CI ran only `make check`, and a newcomer had to clone, install tools and read the Makefile. The roadmap deferred a code package until the same shell logic is copied into a third script ([P4 deferred items](../roadmap.md#p4-mac-mini-bootstrap)); [ADR 0007](0007-stack-contract.md) set a similar trigger for extracting shared Python. That trigger had not fired. The owner wanted the project portable and installable, which is a different reason, so this ADR says so and decides in stages that each stand alone. Since then: 443 tests (`pytest --collect-only`, 2026-11-04), the checks run inside the package, CI is reshaped ([ADR 0019](0019-platform-support-and-ci-matrix.md)).

Requirements and how each is verified:

| ID | Requirement | Verified by |
| :-- | :-- | :-- |
| PK-C1 | No runtime dependency beyond the standard library | Wheel metadata test |
| PK-C2 | One command, `nexahome`, stable exit codes (0 ok, 1 check failed, 2 usage, 3 environment not ready) and `--help` | Unit tests |
| PK-C3 | A ported command matches the shell original before the original is deleted | Golden tests against both, driven by a fake `docker` on `PATH` |
| PK-C4 | Type hints complete; every command has a failure-path test | Review, pytest |
| PK-P3 | Platform-specific code lives in one package, `nexahome.platform` (one module per system) | Test: no other `sys.platform` or `uname` use |

## Decision
**Languages.** POSIX `sh` for glue only, small (about 30 lines), ShellCheck-clean in CI, no logic duplicated across scripts. Python **3.13 or newer** (owner's choice) for anything with logic: standard library only at runtime, `argparse` for the CLI. Build backend hatchling, build-time only. Dev tools: pytest, pinned in the `dev` dependency group of `pyproject.toml` (the check tools are in `check`) per [ADR 0003](0003-project-local-tooling.md); each is still asked about before it is installed. Version policy: `requires-python >=3.13`; CI tests 3.13 and 3.14; a version is dropped at end of life with a changelog note.

**Stages, each a stop point.** Stopping after any stage leaves the repository coherent.
1. `nexahome doctor` and the test harness (fake `docker`). Additive; also useful alone.
2. Bundled stacks and `nexahome init`; the two Python checks move into the package ([ADR 0020](0020-instance-install-and-release-model.md)).
3. `upgrade` and the release pipeline.
4. Run-path ports (`up`, `backup`, `smoke`, `deploy`). A test, not a ban: while the mini is in the vendor's return window, new code may be added beside an old script that stays untouched, with golden tests (read-only logic such as `smoke` parsing is the example). Switching a caller (Makefile, hook, CI) to the package, and porting commands that change data or hosts (`up`, `backup`, `restore`, `deploy`), wait until Track B step B2 has closed, because B2 tests ADRs 0014 to 0017 on that run path. (Hooks and CI were released to call the package on 2026-11-03 at the owner's request; the run-path scripts are untouched.) Each old script stays until golden tests pass and is deleted in its own commit.

The Makefile stays as one-line shims, so documented `make` commands keep working. This amends by reference the Confirmed run-path rule in ADR 0007 ("Make and POSIX shell; Python for checks only") and the register row "no `pyproject.toml` until Python code needs it" (Python code now needs it, from stage 1). ADR 0007 line 14 now points here and the register row says `pyproject.toml` exists (both edited on 2026-11-03 at the owner's yes); the run-path rule itself is superseded only if this ADR is decided.

## Consequences
Easier: tested logic, one install path, the same code on a laptop, the mini and CI, errors that end in a command. Harder: the first Python package and build step in the repository; a solo maintainer carries the package; Python 3.13 is newer than Ubuntu 24.04's 3.12, so non-uv users must supply it and the docs lead with uv. **Unverified:** that `uv tool install <wheel URL>` fetches Python 3.13 by itself (not run as of 2026-11-03: the PK6 timed run used a cached Python); `make setup` on the macOS system Python 3.9.6. Hatchling `force-include` was tried and replaced by `include` plus `sources`, because it shipped a local `.env` and the stack READMEs.

Failure modes: wrong Python → pip refuses the wheel before `doctor` can run (`make setup` names the fix; `doctor` only prints the interpreter version); Docker missing → stack commands stop with the start hint, `check` and `--version` still work; a port changes behaviour → old script kept until golden parity. Evolution: the CLI contract is the same on laptop, mini, Linux host and NAS; only environment variables change.

## Alternatives
| Option | Verdict |
| :-- | :-- |
| Keep shell and scripts, add tests with bats | Rejected: another tool, still no portable parsing or exit-code contract |
| click or typer | Rejected: runtime dependency |
| Go single binary (for this package) | Rejected: owner does not know Go; maintenance risk. Languages for application stacks are a separate question, see [ADR 0022](0022-own-images-and-app-stacks.md) |
| C++ helper | Not built. Trigger: a measured need Python misses; then a separate executable with a JSON contract, never an in-process extension |
| Python floor 3.11 or 3.12 | Not taken: owner chose 3.13; lowering later breaks nobody |
| ruff or a type checker now | Not proposed; added when a lint need shows up |
| Wait for the third-copy trigger | Not taken: portability and install are reasons the trigger did not cover |
