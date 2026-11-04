# 0022. Own images and application stacks

* **Status:** Proposed (nothing built; not measured on an engine)
* **Date:** 2026-11-04

## Context
Six of the seven stacks run an upstream image unchanged. The seventh, `gatus`, adds a thin local layer because upstream is `scratch` ([ADR 0013](0013-health-view.md)). The roadmap's P8 plans applications the owner writes (an expense tracker, portfolio tracking), and the register already names Actual Budget the reference client and drill subject, not the final expense app ([ADR 0009](0009-first-app-actual-budget.md)). An app of the owner's own is the first stack that builds from source, so three questions need an answer before the first one is written: when to build instead of adopt, what a built stack must provide whatever language it is written in, and what the package does about it.

The Compose policy ([constraints](../constraints.md#compose-policy)) already enforces most behaviour: pinned tag, health check, restart, loopback ports, non-root numeric `user`, `cap_drop: [ALL]`, `no-new-privileges`, read-only root, no host namespaces, no `devices`. It has no rule about `build:`: a hypothetical profile written to the contract below passes `nexahome check` unmodified, and so does one with `build: .`, whose context would hold `.env` (scratch folder, Docker CLI only, no engine, 2026-11-03). Only the CLI and its checks are Python ([ADR 0018](0018-code-package-and-language-strategy.md)); app stacks are images, so their language is a separate choice that must not leak into the contract.

## Requirements
State of the check: **enforced** by `nexahome check` today; **test** to extend; **review** until a rule exists; **engine** needs a running engine (not run for this ADR).

| ID | Requirement | Verified by |
| :-- | :-- | :-- |
| AS-1 | A stack builds its own image only when no maintained upstream image fits; the README says why | Review (README row, pull request) |
| AS-2, 6, 7, 9, 10, 11 | Everything the Compose policy ([constraints](../constraints.md#compose-policy)) and the [runbook](../runbooks/add-a-stack.md) already require; not restated | `nexahome check`, `make smoke` |
| AS-3 | Base image by exact tag; one lockfile for the ecosystem; one Dependabot entry for the Dockerfile and one for the lockfile's ecosystem | Test: extend the Dependabot coverage test in `tests/test_docs.py` |
| AS-4 | The build context is `./app`, never the stack folder, and a `.dockerignore` exists, so `.env` cannot enter an image layer | Review; candidate policy rule |
| AS-5 | The local image is named `nexahome/<directory>:local` with `pull_policy: build`, so the name is never pulled | Review; candidate policy rule (precedent: `gatus`) |
| AS-8 | The process stops cleanly on SIGTERM (handles it, or Compose `init: true`) | `docker compose stop` returns inside the default grace period: engine |
| AS-12 | The package stays standard-library only; templates are data under `stacks/`; any new command follows [ADR 0021](0021-command-line-performance.md) and gets a budget row | `tests/test_packaging.py`, `tests/test_startup.py` |
| AS-13 | The contract text needs no language; language appears only in a profile | Review of this ADR and each profile |

## Decision
**Adopt before build.** A stack builds only under AS-1. Per image today: `hello` (busybox), `actual` ([0009](0009-first-app-actual-budget.md)), `backup` (restic, [0008](0008-backup-tool.md)), `edge` (Caddy, [0011](0011-edge-and-local-hostnames.md)), `identity` (Pocket ID, [0010](0010-identity-provider.md)) and `portal` (Homepage, [0012](0012-portal.md)) are adopted; `gatus` is a thin build on upstream. Future: the owner's expense app is built (nothing upstream is theirs); portfolio tracking, local AI, home automation and media are adopt candidates, not evaluated here. Adopting upstream software is independent of its language (Gatus, Caddy and Pocket ID are Go).

**The contract is behavioural.** An app stack provides the contract in any language. It is checked by the Compose policy and `make smoke`, which look at behaviour, not at the language. A language adds a *profile*: a template stack that satisfies the contract with that runtime's base, build, lockfile and health form.

**Profiles** (the owner's choice; others wait for a trigger):

| Runtime | When | Final image | Build and lockfile | Dependabot | Health form | Not verified |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| Python, FastAPI | first | official `python` slim, exact tag chosen when the template is written | `pip install --no-cache-dir` of `requirements.txt` pinned with `==` | `docker`, `pip` | Python one-liner on an own `/health` (slim images have no `curl` or `wget`) | idle RAM, one-liner cost, arm64 wheels of the chosen dependencies |
| Python, Streamlit | first | same | same | same | `/_stcore/health` | RAM; needs a writable `HOME` (tmpfs); native OIDC exists (`st.login`, since 1.42) but fixes the scopes at `openid profile email`, so whether Pocket ID's group claim reaches the app is open |

Other runtimes (Node, Go, Rust, C++, static, worker, accelerator): a profile is added when an owner-written app needs one, with its own review; Go only per the 2026-11-03 answer; accelerators need their own ADR and the owner's yes.

**Template layout (Proposed).** Sibling directories `_template-<profile>`; each is a normal stack, so `nexahome check` verifies every profile in CI (AS-2). One rule replaces three hard-coded exclusions: names starting with `_` are not services (`Makefile` line 5, `defaults.NON_SERVICE_STACKS`, used in `stacks/catalogue.py` to pick the default stacks). The alternative, profiles as subfolders of `_template/`, needs no rule but leaves profiles unchecked. Each profile costs two Dependabot entries and a weekly pull request source.

**Staging, each a stop point.**
1. *Stage 0, no package code.* When the first app starts: write its profile template and add an "own image" section to the add-a-stack runbook. Follow-ups that travel with the first profile: the `_` rule, the Dependabot test for two entries, and policy rules for AS-4 and AS-5.
2. *Stage 1, only after a second hand copy shows the rename friction.* `nexahome stacks new <name> --from <profile>`: copies the profile and renames project, service, volume and variables. Standard library only, logic outside `commands/`, imported inside `run` (ADR 0021).
3. *Not planned: a `build` command.* `docker compose up --build` exists; if nothing is built, nothing breaks.

**Where it applies.** App stacks live in the repository, so they belong to the fork path (customisers, [ADR 0020](0020-instance-install-and-release-model.md)). ADR 0020 says runners "add unnamed stacks" but package-owned `stacks/` has no place for them; this ADR does not settle that and records the direction chosen in ADR 0020 (a user-owned folder or `compose.override.yaml`). An app's source is public here: placeholders and dummy data only; its data lives in its volume.

## Consequences
Easier: a new language is a template and two Dependabot entries, not package code or an ADR edit; the same checks run for every profile; the owner's apps start from a hardened base. Harder: each profile is upkeep (a weekly pull request source, a Dockerfile to read); a merged base-image bump changes nothing running until the stack is rebuilt (`up --build`).

**Failure modes (what breaks, what still works)**

| Failure | Effect | Handling |
| :-- | :-- | :-- |
| Build fails (registry unreachable, dependency yanked) | That stack's `up` fails; running stacks and the edge are unaffected | Exact tags and lockfiles; the error names the stack; digest pinning is the trigger if tags move |
| Stale image after a Dependabot merge | The old container keeps running | `up --build`; README line; `nexahome up` (PK7) is the place to make this default |
| Out of memory on the 2 GB VM | Only that container is killed (`mem_limit`) | Idle RAM measured per app; a heavy build or run is one at a time |
| App writes outside tmpfs or its volume | Crash at start, health red, `make smoke` names it | Template provides tmpfs for `/tmp` and `HOME` |
| `.env` copied into an image | Secret in a layer | AS-4 (`./app` context, `.dockerignore`) |
| Compromised app | Contained by non-root, no capabilities, read-only root, no socket, loopback or edge only | Outbound traffic is **not** restricted today; stated, not solved |
| Disk fills with images and build cache (20 GB VM) | Builds and starts fail | Pruning is destructive and needs the owner's yes |
| Edge or portal down | The app still answers on its loopback port | Unchanged |

**Evolution per hardware hop**

| Hop | Changes | Stays |
| :-- | :-- | :-- |
| Laptop (Colima, arm64, 2 GB VM) | One heavy app at a time; build on the host | Template, contract, policy |
| Mac mini (arm64) | Larger VM; same Dockerfile | Everything else |
| Linux host (amd64 or arm64) | Native build from multi-arch bases; no cross-build | Everything else |
| Jetson (arm64 Linux) | CUDA or L4T bases and device access need their own ADR | The contract for CPU-only apps |
| NAS | Data volumes only; `NEXAHOME_BACKUP_DIR` | Backup by label |
| Second host | Build per host until a registry is justified (a second host needing the same image) | Profiles |

**Not built.** Any template directory or code (stage 0 is on the first app); `stacks new` (stage 1); a `build` command; policy rules for AS-4 and AS-5; Go, Rust, Node and C++ profiles; a registry, image push or buildx pipeline; digest pinning; image scanning, Hadolint or any new tool; Cloud Native Buildpacks, `docker init`, Nixpacks or Railpack; GPU access; a per-stack manifest for the edge, portal and Gatus files (trigger in ADR 0020: a third user-added named app); any runtime dependency in the package.

**Confirmed items touched.** None edited. [ADR 0007](0007-stack-contract.md) says "a stack is a copy of `stacks/_template/`"; with profiles it becomes "of `stacks/_template/` or a profile", which would be an amendment by reference when this is decided (the owner's yes). The "Go single binary" row in ADR 0018 concerns the package; this ADR carries the app-stack decision.

## Alternatives
| Option | Verdict |
| :-- | :-- |
| Adopt only, never build | Rejected: the owner's own apps have no upstream |
| One template, language chosen by editing it | Rejected: each language needs a different base, lockfile and health form; the contract would grow language text (AS-13) |
| Cloud Native Buildpacks (`pack`, Paketo) | Not now: a new global tool, opaque builds, arm64 support not found; trigger: three or more hand-kept profiles |
| `docker init` | Not now: a Docker Desktop feature per the sources, not checked against Colima; the idea (a template per language) is adopted |
| A `nexahome build` command | Rejected: `docker compose up --build` exists |
| Registry for images | Deferred: needs a second host |
| Python only, ever | Rejected as a rule: the contract is language-neutral; Python is first, not exclusive |

Not verified: idle RAM and image size of any profile; the health one-liner's cost; arm64 wheels for the chosen dependencies; Streamlit and Pocket ID group claims; `pull_policy: build` against the official Compose specification (secondary sources only); read-only root behaviour of shell-less images; Dependabot support for Conan and CMake (not seen in the ecosystem list, which was read in two parts); `pack` and Paketo on arm64; `docker init` under Colima; anything on a running engine.

## Owner answers (2026-11-03)
Accepted as recommended: (1) Go only for upstream software, an owner-written Go profile waits for a measured need and an explicit yes; (2) sibling `_template-<profile>` folders; (3) the first app's sign-in is loopback only until the group claim is proven, then native OIDC; (4) no profile after Python until an app needs one. (5) Where a runner's own stacks live stays an open gap in [ADR 0020](0020-instance-install-and-release-model.md). The ADR is Proposed: nothing here is Confirmed, and the amendment to [ADR 0007](0007-stack-contract.md) waits for a separate explicit yes.
