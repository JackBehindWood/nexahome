# 0007. Stack contract

* **Status:** Proposed
* **Date:** 2026-10-21

## Context
Backups, upgrades and tooling must treat every stack the same, without knowing stack names. New stacks should be a copy, not a design exercise.

## Decision
- A stack is a copy of `stacks/_template/`: `compose.yaml`, `.env.example`, README with measured RAM and disk, 24/7 need, what is backed up and how to verify a restore.
- Every named volume carries the label `nexahome.backup` with `"true"` or `"false"`. Backup tools find data by label.
- The Compose project name is `nexahome-<directory>`. Both rules are enforced by `make check`.
- `make up` creates `.env` from `.env.example` when absent and stops while a value is `CHANGE_ME`. `up`, `down` and `ps` without `STACK` act on every stack except `_template` and `backup`.
- Run-path code is Make and POSIX shell; Python is for checks only. Trigger: when a second Python consumer appears (S2 `make status`, S3 `make upgrade`), extract a stdlib-only `scripts/stacks.py`.

## Consequences
Adding a stack is a copy and `make check`. Backup scripts need no stack list. Removing a volume label breaks the check, not a backup.

## Alternatives
A list of stack names in the backup script (drifts), a generator script (a copy is enough), a shared Python module now (one consumer), a compiled tool (toolchain cost, ADR 0003).
