# 0020. Instance, install and release model

* **Status:** Proposed (`init`, `config` and the manifest are built; `upgrade` is rehearsed, not built; the design as a whole is not decided)
* **Date:** 2026-11-02

## Context
Today a user clones the repository, runs `make setup` and edits files in the tree. [ADR 0006](0006-concerns-and-audiences.md) defines an instance as a checkout plus untracked state and rejected an `instance/` directory for lack of a reader who needed it. A reader now exists: someone who wants to run NexaHome as shipped without cloning. The code package ([ADR 0018](0018-code-package-and-language-strategy.md)) can serve them, but three files (`edge` Caddyfile, `portal` services, Gatus targets) list every named app, so a package-owned `stacks/` cannot also be edited per app.

Requirements and how each is verified:

| ID | Requirement | Verified by |
| :-- | :-- | :-- |
| PK-I1 | From "uv installed" a cold user reaches a running `hello` in 5 minutes; the no-uv path (Python 3.13 present) also works, time recorded | Timed run in a clean Linux container and a fresh `HOME` |
| PK-I2 | `doctor` names the exact next command for each failure | Table-driven test |
| PK-I3 | Upgrade never touches `.env`, data or backups and can be rolled back | Rehearsal: init at version A, upgrade to B, compare fingerprints, roll back |
| PK-I4 | Uninstall removes the tool and leaves the instance, and prints the command | Rehearsal |
| PK-S1 | `init` and `upgrade` never overwrite user-owned files; secrets use `secrets`, mode 600, never printed | Unit tests |
| PK-S2 | No network access except `docker` and an explicit `nexahome update` (release feed and assets over https, checksum-verified); no telemetry; no archive extraction | Code review; a test that only `net.py` imports network modules; tests with the network blocked |
| PK-R1 | A tag builds a wheel and sdist with checksums, installable from the release URL | Dry-run on a branch, install in a scratch environment |
| PK-R2 | The wheel contains the stacks and `init` output passes `nexahome check` | Wheel round-trip test in CI |

## Decision
**Two audiences, one honest line.** *Runners* use NexaHome as shipped, make their own stacks with `nexahome stacks new`, in `stacks/<name>` beside the package's; ownership is by name (the bundle and the manifest), so package stacks stay untouched and a later `upgrade` never replaces a user's (built 2026-11-04; `stacks.d/` was rejected because the backup job mounts `stacks/` only; how `nexahome up` and `upgrade` treat them is not built). *Customisers* fork the repository; this stays the register's audience ("a blueprint to read and fork"). The README says so plainly. Deferred with a trigger: a per-stack manifest from which the CLI renders the three aggregator files, when a third user-added named app appears.

**Install.** `uv tool install <release URL>` (recommended; optional), or `python3.13 -m venv` plus `pip install <wheel>`. Installing uv, Docker or Colima stays the user's step, documented, never scripted. Release assets are a wheel, an sdist and checksums, published on GitHub; install docs verify with a command that works on macOS and Linux. PyPI and provenance attestations wait for a stable tag and a name check. First tag `v0.2.0` (the package version); the docs set stays 0.x, so the two numbers are independent. This changes the Proposed docs convention "1.0 reserved for the first release tag"; the owner agreed on 2026-11-02, the wording changes when this ADR is decided.

**Instance.** Home resolves in order: `--home`, `$NEXAHOME_HOME`, the nearest parent holding `nexahome.toml` or a NexaHome checkout, else `~/nexahome` if it holds `nexahome.toml` (under `$HOME` because Colima mounts only the home directory). A git clone is an instance Git tracks, so contributors and the mini's deploy checkout ([ADR 0017](0017-deploy-flow.md)) need no second path; `init` and `upgrade` refuse inside a checkout and say "use git pull". Layout: `nexahome.toml` (schema 1, stack list; minimal at stage 2), package-owned `stacks/` (never edited; changes go in `.env` or `compose.override.yaml`), per-stack `.env`, `data/`. `init` writes a hash manifest; the guarded replace arrives with `upgrade` at stage 3. Compatibility: a newer schema is refused with the upgrade command; new variables have defaults; a removed command warns for one minor release first.

**Stacks stay single-sourced:** `stacks/` remains in the repository and the build includes it as package data; stack READMEs are left out because their relative links break.

**Scope notes.** [ADR 0003](0003-project-local-tooling.md) governs developing NexaHome; the product is one uv tool in its own environment, removable by one command. ADR 0006's update promise gets its reader and tag from this model, and its `instance/` rejection is revisited by reference. Neither Confirmed ADR is edited until the owner says yes.

## Consequences
Easier: a 5-minute path, tested upgrades, the same code path for clones and installs. Harder: a guarded replace rather than a merge, so a user who edits package files is told to move the change into an override; two numbering schemes; a release process to maintain. Failure modes: wheel built without `stacks/` → round-trip test blocks the release; upgrade interrupted → staged and atomically renamed, previous copy kept; GitHub unreachable → the installed tool and instance keep working. Evolution: NAS sets `NEXAHOME_BACKUP_DIR`; a second host gets its own `nexahome.toml`.

Unverified: hash on a direct wheel URL in uv; hatchling `force-include` was replaced by `include` plus `sources` (it shipped a local `.env`); uv fetching Python 3.13; WSL2.

## Alternatives
| Option | Verdict |
| :-- | :-- |
| `uv tool` or pipx plus a release wheel | Adopted |
| Copier or cruft diff-merge updates | Idea adapted (hash guard plus overrides); the tool rejected: runtime dependency, merge conflicts hard for non-experts |
| Cookiecutter | Rejected: generate-only |
| Umbrel or CasaOS-style app store, Helm | Rejected: far larger than a few Compose stacks |
| Homebrew tap, `curl \| sh`, single binary | Rejected: global install or unreviewable code; against ADR 0003 |
| PyPI now | Deferred: needs a stable tag and a name check |
| Three-way merge on upgrade | Not built |
