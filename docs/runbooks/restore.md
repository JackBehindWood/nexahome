# Restore a stack from backup

**Audience:** anyone running NexaHome. **Admin rights needed:** no. Needs the container runtime running, the repository and the saved password. Tool: restic 0.19.1 (pinned in [stacks/backup/compose.yaml](../../stacks/backup/compose.yaml); [ADR 0008](../adr/0008-backup-tool.md)).

Check that a backup restores, without touching your live data (replace `actual` with your stack):

```sh
make snapshots                                   # list snapshots (the newest is used by default)
make restore STACK=actual TARGET=check           # restore into a separate copy
(cd stacks/actual && ACTUAL_PORT=5007 docker compose -p nexahome-actual-check up -d --wait)   # a free port
# open http://127.0.0.1:5007 and look for something you know is there, then remove the copy:
(cd stacks/actual && docker compose -p nexahome-actual-check down -v)
```

Expected output of the restore: `restoring <volume> into volume nexahome-actual-check_data`, then `finished verifying N files`, then `Restored into project ...` with the start and remove commands. If it ends with an error it prints the command that removes the partial copy.

Remove the copy when you are done. It carries the backup label, so the next `make backup` would save it as a stack of its own.

## Restore never overwrites

`make restore` refuses when the target volume exists. It creates new volumes (from the app image, so they get the app's ownership) and fills them. It also restores the stack's `.env` when none exists; it never replaces one.

- `SNAPSHOT=<id>` restores an older snapshot (ids from `make snapshots`).
- `TARGET=<suffix>` restores into a separate project `nexahome-<stack>-<suffix>`; leave it out to restore under the original name.

## Replace live data with a backup

Use this when the data is lost, damaged, or you want to go back (for example after a failed upgrade). The volume is deleted by you, on purpose; there is no flag that does it.

```sh
make down STACK=actual
docker volume rm nexahome-actual_data     # the live data; make sure the snapshot is the one you want
make restore STACK=actual                 # add SNAPSHOT=<id> for an older one
make up STACK=actual
```

## New machine, or the working copy is gone

1. Clone the repository and start the container runtime ([README](../../README.md)). The first run needs network access to pull the images.
2. Put your saved password file at `.config/restic-password` (`mkdir -p .config`, then copy it in, then `chmod 600 .config/restic-password`).
3. Put the repository directory where `NEXAHOME_BACKUP_DIR` points (default `data/backup`; set the variable if it lives elsewhere, such as an external disk). It must be inside your home directory on macOS ([stacks/backup/README.md](../../stacks/backup/README.md)).
4. `make restore STACK=<name>` for each stack, then `make up STACK=<name>`.

## If the password is lost

Nothing can recover it: restic encrypts the repository, and without the password every snapshot is unreadable. Delete the repository, run `make backup-init` again, and keep a copy of the new password somewhere other than this laptop.

## Evidence

Drill of 2026-10-21 (laptop, same disk, Actual with dummy data, 4 files, 2 snapshots, repository 64 KB): restore into a new project from a fresh clone and a copy of the repository took about 2 seconds, `--verify` clean, a fingerprint of ownership, mode and content equal to the original, the known budget item visible. Deleting the live volume and restoring it under its own name took about 2 seconds with the same result. `restic check --read-data` was clean. Figures grow with the data. This was a drill on one disk, not protection; see [architecture](../architecture.md#data-backup-and-restore).
