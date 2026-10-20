# 0002. Branching model

* **Status:** Confirmed
* **Date:** 2026-10-20

## Context
A solo public repository where work should stay isolated until verified.

## Decision
`main` is stable and published; `dev` is the integration branch; each piece of work lives on `feat/<topic>` with small commits (`docs:`, `feat:`, `fix:`, `chore:`). Commits on `feat/*` are allowed once verification passes. Commits to `main`, any merge (including into `dev`), and any push need explicit approval from the owner. Merges into `main` happen only through pull requests, enforced by GitHub branch protection (applies to the owner too; no force-push, no deletion). Outside contributors change any branch, including `dev`, through pull requests from forks.

## Consequences
Clear history and a safe `main`. Slightly more ceremony per change.

## Alternatives
Trunk-based development on `main` (simpler, less isolation); feature branches with pull requests only (more ceremony for a solo project).
