# 0019. Platform support and CI matrix

* **Status:** Proposed (the jobs are written in `ci.yml`; only the results listed under Evidence are measurements)
* **Date:** 2026-11-02

## Context
The register says macOS and Linux are supported, and the scope line says "Windows is not a target". Today CI runs `make check` on one Ubuntu job only, so portability is a claim, not evidence: no macOS job, no arm64 job, GNU make 3.81 (macOS) and 4 (Linux) never compared. The code package ([ADR 0018](0018-code-package-and-language-strategy.md)) needs the same evidence.

Requirements and how each is verified:

| ID | Requirement | Verified by |
| :-- | :-- | :-- |
| PK-P1 | Commands that need no container engine behave the same on macOS arm64, Ubuntu amd64 and Ubuntu arm64 | Platform jobs green on a pull request into `main` and in the weekly run (not on every pull request) |
| PK-P2 | Engine behaviour is proven on Linux in CI and by hand on the laptop and the mini | Linux job runs `hello` up and down; macOS proof recorded in the session log |
| PK-P3 | Platform-specific code lives in one package, `nexahome.platform` (one module per system), and is documented | Test (see ADR 0018) |
| PK-P4 | WSL2 is documented as Linux; native Windows is refused with a clear message | Unit test, doc review |

## Decision
- **Supported:** macOS and Linux, amd64 and arm64. WSL2 counts as Linux, best effort, no CI job. Native Windows is unsupported and refused with a message that points to WSL2. This rewords the Confirmed scope line "Windows is not a target"; the line is not edited until the owner says yes.
- **Two tiers** (job names stay stable; reshaped after the macOS runner queue held up pull request 22). A `plan` job decides what runs, by a job-level `if` (never a workflow-level `paths` filter, which would leave a required check pending). The **fast set** runs on every pull request, push and manual run: the two required checks (below), `portable (ubuntu-amd64)`, `hello up and down (ubuntu-amd64)`, `tests (ubuntu-amd64, py3.13)` and `py3.14`, and `gate`. A pull request that changes only `docs/`, Markdown files or `LICENSE` skips `portable`, `hello` and `tests`. The **platform set** runs on a pull request into `main`, weekly and on a manual run: `portable` and `tests` on `ubuntu-arm64` and `macos-arm64` (`tests` on Python 3.13, and 3.14 on macOS), and `platforms`, an informational job that reports them. Each platform job runs on Python 3.13 (the project minimum, installed with `actions/setup-python`): shell syntax checks, ShellCheck at warning severity, `make setup` and `make check`; `tests` runs pytest, `nexahome doctor` on the Linux runners (they have a Docker engine) and a wheel-contents listing. macOS uses its own make (3.81 on the laptop; the runner prints its version). Newer pushes cancel older runs of the same pull request.
- **Engine:** hosted macOS runners cannot run Colima or Docker (no nested virtualisation, [runner-images issue](https://github.com/actions/runner-images/issues/9254)), so there the fake-`docker` tests stand in. The Linux amd64 job runs `hello` up, healthy, down.
- **Arm64 Linux runners** are generally available and free for public repositories since August 2025 ([GitHub changelog](https://github.blog/changelog/2025-08-07-arm64-hosted-runners-for-public-repositories-are-now-generally-available/)). The arm64 job is the first to drop if it proves flaky: it exists for the Jetson and arm64 Linux hops.
- **Required checks:** `secrets` and `checks` keep their names and stay required. `gate` succeeds only when the fast set did: it fails if `plan` or any fast job failed or was cancelled, and never waits for a platform job, so a runner queue cannot hold a merge. `gate` has been required since 2026-11-02 (a GitHub setting); `platforms` is never required. GitHub runs `schedule` only on the default branch, so the weekly run tests `main` and starts once this workflow is on `main`; a manual run (`workflow_dispatch`) is the fallback, and GitHub disables schedules of a public repository after 60 days without activity.
- **Portability traps (PK3):** `sha256sum` appears once in the repository, inside the restic container (`scripts/backup.sh`, fingerprint), so it never runs on the host; every platform job prints which of `shasum` and `sha256sum` exists, and docs that print a checksum should use `shasum -a 256` (PK9). `make setup` enforces the Python 3.13 minimum: without `uv` it stops early with the version found; with `uv` it asks for `>=3.13`.
- **macOS and Compose policy:** `nexahome check` needs the Docker CLI with the Compose plugin but no engine, so the macOS job installs the CLI on the throwaway runner when it is missing and runs the full `make check`. If that install fails, the job falls back to the hook checks and the gap is logged.
- **WSL2 (best effort, not tested):** treat the distribution as Linux with Docker Engine inside it, and keep the checkout on the Linux filesystem. Native Windows is refused with a message that names WSL2 (`nexahome.platform`, unit-tested with an injected host; native Windows itself is not tested).

## Consequences
Easier: portability becomes a green or red fact; a platform gap shows up in CI, not at a user's desk. Harder: more CI configuration and minutes (free on public repositories); macOS runner differences can produce false reds. Failure modes: arm64 or macOS runner unavailable → the platform check stays pending, finding logged, required checks and `gate` unaffected; a platform job queued or renamed → `gate` keeps the merge path open. Evolution: the Mac mini (macOS arm64, Colima) and a Linux host (Docker Engine) differ only in the runtime, which `nexahome.platform` isolates.

## Evidence (PK3, local, 2026-11-02)
- ShellCheck 0.11.0 on the four scripts: exit 0 at `--severity=warning` and `--severity=error`; 13 notes at info and style level (`backup.sh` SC1091, SC2012, SC2016; `smoke.sh` SC2016, SC2015, SC2116, SC2086), left as they are because the scripts are on the run path.
- `sh -n` and `dash -n` pass on all four scripts; GNU make 3.81 runs `make check` on the macOS arm64 laptop.
- `scripts/setup.sh`, rehearsed in scratch copies: a `python3` reporting 3.12 without `uv` stops with the version and one next step; with `uv` the environment is created on Python 3.14.7 (`>=3.13` accepted); a 3.14 `python3` without `uv` passes the check and installs the pinned tools.
- Read-only GitHub settings: `main` requires `checks`, `secrets` and `gate` (since 2026-11-02), branches up to date, no force pushes.

Unverified: macOS runner details beyond the sources above; `shasum` on minimal Linux images; make 4 differences beyond syntax; WSL2 behaviour; whether the runners ship ShellCheck and a Docker CLI (the first CI run answers this and is recorded in the session log). Freeze rule: no run-path change before B2 closes ([ADR 0018](0018-code-package-and-language-strategy.md)); workflow changes need the owner's approval, and pushing a branch to run CI needs a yes.

## Alternatives
| Option | Verdict |
| :-- | :-- |
| Native Windows support | Not built: no hardware, no user, high cost |
| Self-hosted runners | Rejected: public repository (see roadmap P4) |
| Docker on hosted macOS via third-party actions | Rejected: unreliable without nested virtualisation |
| Matrix without `gate` | Allowed if the owner declines `gate`; merges then depend on stable job names |
| One `gate` that waits for every job | Rejected: a macOS runner queue of 5 to 15 minutes held merges into `dev` |
| Workflow-level `paths` filter for docs-only changes | Rejected: the workflow does not start and a required check stays pending |
| Test only on Linux | Rejected: the laptop and mini are macOS |
