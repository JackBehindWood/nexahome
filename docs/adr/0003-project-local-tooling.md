# 0003. Project-local tooling and opt-in git hooks

* **Status:** Confirmed
* **Date:** 2026-10-20

## Context
The development machine should stay clean, and setup should be reproducible and portable between macOS and Linux.

## Decision
Dev tools are pinned in `requirements-dev.txt` and installed in a gitignored `.venv`. No global or Homebrew installs without a clear technical reason and the owner's approval. Standalone binaries run in CI or repo-locally. Optional linters and formatters are added only when needed. Git hooks are never installed silently: the dependencies, install location, global impact, and removal steps are explained first, and installation is opt-in.

## Consequences
Reproducible and removable by deleting `.venv`. Tools that need a standalone binary run in CI instead of locally.

## Alternatives
Global installs via Homebrew or pipx (faster, but pollute the machine and drift between hosts).
