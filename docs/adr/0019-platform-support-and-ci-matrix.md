# 0019. Platform support and CI matrix

* **Status:** Proposed (the matrix is not built; no result here is a measurement)
* **Date:** 2026-11-02

## Context
The register says macOS and Linux are supported, and the scope line says "Windows is not a target". Today CI runs `make check` on one Ubuntu job only, so portability is a claim, not evidence: no macOS job, no arm64 job, GNU make 3.81 (macOS) and 4 (Linux) never compared. The code package ([ADR 0018](0018-code-package-and-language-strategy.md)) needs the same evidence.

Requirements and how each is verified:

| ID | Requirement | Verified by |
| :-- | :-- | :-- |
| PK-P1 | Commands that need no container engine behave the same on macOS arm64, Ubuntu amd64 and Ubuntu arm64 | CI matrix green on all three |
| PK-P2 | Engine behaviour is proven on Linux in CI and by hand on the laptop and the mini | Linux job runs `hello` up and down; macOS proof recorded in the session log |
| PK-P3 | Platform-specific code lives in one module, `platform.py`, and is documented | Test (see ADR 0018) |
| PK-P4 | WSL2 is documented as Linux; native Windows is refused with a clear message | Unit test, doc review |

## Decision
- **Supported:** macOS and Linux, amd64 and arm64. WSL2 counts as Linux, best effort, no CI job. Native Windows is unsupported and refused with a message that points to WSL2. This rewords the Confirmed scope line "Windows is not a target"; the line is not edited until the owner says yes.
- **Matrix** (job names stay stable): Ubuntu amd64, Ubuntu arm64, macOS arm64. Each runs shell syntax checks, ShellCheck, the existing checks and, once it exists, pytest. macOS also runs the checks under make 3.81. Python 3.13 and 3.14 on Linux, 3.14 on macOS.
- **Engine:** hosted macOS runners cannot run Colima or Docker (no nested virtualisation, [runner-images issue](https://github.com/actions/runner-images/issues/9254)), so there the fake-`docker` tests stand in. The Linux amd64 job runs `hello` up, healthy, down.
- **Arm64 Linux runners** are generally available and free for public repositories since August 2025 ([GitHub changelog](https://github.blog/changelog/2025-08-07-arm64-hosted-runners-for-public-repositories-are-now-generally-available/)). The arm64 job is the first to drop if it proves flaky: it exists for the Jetson and arm64 Linux hops.
- **Required checks:** `secrets` and `checks` keep their names and stay required. An optional `gate` job that succeeds only when every matrix job does is added; whether `gate` becomes required is the owner's decision in PK3 (a GitHub setting), because renaming or removing a required matrix job otherwise freezes merges.
- **Portability traps to settle with evidence in PK3:** `shasum -a 256` versus `sha256sum`; whether `make setup` works on the macOS system Python 3.9.6 (the package itself needs 3.13).

## Consequences
Easier: portability becomes a green or red fact; a platform gap shows up in CI, not at a user's desk. Harder: more CI configuration and minutes (free on public repositories); macOS runner differences can produce false reds. Failure modes: arm64 runner unavailable → job dropped, finding logged, required checks unaffected; matrix job renamed → `gate` keeps the merge path open. Evolution: the Mac mini (macOS arm64, Colima) and a Linux host (Docker Engine) differ only in the runtime, which `platform.py` isolates.

Unverified: macOS runner details beyond the sources above; `shasum` on minimal Linux images; make 4 differences beyond syntax; WSL2 behaviour. Freeze rule: no run-path change before B2 closes ([ADR 0018](0018-code-package-and-language-strategy.md)); workflow changes need the owner's approval, and pushing a branch to run CI needs a yes.

## Alternatives
| Option | Verdict |
| :-- | :-- |
| Native Windows support | Not built: no hardware, no user, high cost |
| Self-hosted runners | Rejected: public repository (see roadmap P4) |
| Docker on hosted macOS via third-party actions | Rejected: unreliable without nested virtualisation |
| Matrix without `gate` | Allowed if the owner declines `gate`; merges then depend on stable job names |
| Test only on Linux | Rejected: the laptop and mini are macOS |
