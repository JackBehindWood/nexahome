# backup

A one-shot [restic](https://restic.net) job that backs up every volume labelled `nexahome.backup: "true"` and each backed-up stack's `.env` into an encrypted repository on the host ([ADR 0008](../../docs/adr/0008-backup-tool.md)). It is never started by `make up`; `make backup` runs it.

```sh
make backup-init     # once: creates the repository and the password file
make backup          # every stack, or STACK=actual
make snapshots       # list what is saved, with sizes
make verify          # stacks stopped: compare each volume with a restored copy, then remove the copy
make backup-check    # read the whole repository (READ=1/10 reads a tenth)
make restore STACK=actual   # restore into new volumes (TARGET=suffix for a copy, SNAPSHOT=id for an older one)
make status          # stack health, how recent the last snapshot is, repository size
```

Each stack is stopped for a consistent copy (a few seconds), saved as one snapshot tagged `stack=<name>`, then started again. `restic check` runs at the end. `make restore STACK=actual` brings a stack back into new volumes and never overwrites ([restore runbook](../../docs/runbooks/restore.md)). A restore drill passed on 2026-10-21 with dummy data; keep to dummy data until you have run it on your own setup.

**Save the password.** `make backup-init` writes a random password to `.config/restic-password` in this repository (mode 600, gitignored, never committed) and never prints it. Copy that file into a password manager. Losing it makes every snapshot unreadable, and deleting the repository folder deletes it too. To keep it elsewhere, set `NEXAHOME_RESTIC_PASSWORD_FILE`.

| Item | Value |
| :--- | :--- |
| RAM, disk | RAM not measured (the job runs for seconds); repository 64 KB for the Actual drill data and 2 snapshots; it grows with your data, deduplicated and compressed (a repeat run added 684 B) |
| Must run 24/7? | no; runs for seconds to minutes when you call it |
| Backed up | not itself; it holds the repository, which is a directory on the host |
| Verify | `make backup` ends with `backup ok`; the restore drill is the real proof ([runbook](../../docs/runbooks/restore.md)) |

## Where the repository lives

Default: `data/backup` in this repository (gitignored, visible, and removed by deleting that folder). It is on the same disk as your data, which makes it a drill, not protection. `make status` shows its size. Set `NEXAHOME_BACKUP_DIR` (shell or `stacks/backup/.env`, see `.env.example`) to put it elsewhere, such as an external disk. A Docker volume is deliberately not used: it would sit in the Colima VM's small disk, out of sight, and `colima delete` would remove it together with the data.

On macOS the container runs in the Colima VM, which shares only your home directory by default. A directory outside it is not shared: Docker silently creates an empty directory inside the VM instead, and the repository would vanish with `colima delete`. `make backup-init` detects this and stops. To share another directory, list the home directory too (naming any `--mount` replaces the default) and restart Colima:

```sh
colima stop
colima start --cpu 2 --memory 2 --disk 20 --mount "$HOME:w" --mount "/path/to/backup-disk:w"
```

Colima saves this in its own profile (`~/.colima/default/colima.yaml`). To undo it, restart Colima without the extra mount and set `mounts: []` there.

## Removing the backups

Restic makes its files read-only, so a plain `rm -r` asks about every file. To delete the repository and the password (all snapshots become unrecoverable), run `rm -rf data/backup .config` yourself.

## Limits

- The job runs as the owner of each volume (uid:uid, read from the volume with `stat`; `NEXAHOME_BACKUP_UID` is only the default for the repository checks). Needed because Pocket ID's volume is 65532, mode 700: with the old fixed uid 1001 the identity backup silently saved only its `.env` (found in the S5 drill, 2026-10-23). No root and no capabilities. A stack with volumes of different owners is not handled (the first volume decides); the first such stack needs a decision.
- Tested on macOS with Colima (virtiofs). On Linux, bind-mounted directories keep their real owner, so the repository directory must be writable by `NEXAHOME_BACKUP_UID`; not tested.
- Retention is manual: `sh scripts/backup.sh restic forget --keep-daily 7 --keep-weekly 4 --keep-monthly 6 --prune`. The same form runs any other restic command (`restic` arguments after the word `restic`).
