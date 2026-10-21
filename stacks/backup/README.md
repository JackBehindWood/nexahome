# backup

A one-shot [restic](https://restic.net) job that backs up every volume labelled `nexahome.backup: "true"` and each backed-up stack's `.env` into an encrypted repository on the host ([ADR 0008](../../docs/adr/0008-backup-tool.md)). It is never started by `make up`; `make backup` runs it.

```sh
make backup-init     # once: creates the repository and the password file
make backup          # every stack, or STACK=actual
make status          # stack health and how recent the last snapshot is
```

Each stack is stopped for a consistent copy (a few seconds), saved as one snapshot tagged `stack=<name>`, then started again. `restic check` runs at the end. Restoring is session 3 of the persistence phase; until a restore has been tested, treat the backup as unproven and keep to dummy data.

**Save the password.** `make backup-init` writes a random password to `.config/restic-password` in this repository (mode 600, gitignored, never committed) and never prints it. Copy that file into a password manager. Losing it makes every snapshot unreadable, and deleting the repository folder deletes it too. To keep it elsewhere, set `NEXAHOME_RESTIC_PASSWORD_FILE`.

| Item | Value |
| :--- | :--- |
| RAM, disk | not measured yet; the repository grows with your data, deduplicated and compressed (second run of the Actual test added 350 B) |
| Must run 24/7? | no; runs for seconds to minutes when you call it |
| Backed up | not itself; it holds the repository, which is a directory on the host |
| Verify | `make backup` ends with `backup ok`; a restore test is the only real proof |

## Where the repository lives

Default: `~/.local/share/nexahome-backup` on the same disk as your data, which makes it a drill, not protection. Set `NEXAHOME_BACKUP_DIR` (shell or `stacks/backup/.env`, see `.env.example`) to put it elsewhere, such as an external disk.

On macOS the container runs in the Colima VM, which shares only your home directory by default. A directory outside it is not shared: Docker silently creates an empty directory inside the VM instead, and the repository would vanish with `colima delete`. `make backup-init` detects this and stops. To share another directory, list the home directory too (naming any `--mount` replaces the default) and restart Colima:

```sh
colima stop
colima start --cpu 2 --memory 2 --disk 20 --mount "$HOME:w" --mount "/path/to/backup-disk:w"
```

Colima saves this in its own profile (`~/.colima/default/colima.yaml`). To undo it, restart Colima without the extra mount and set `mounts: []` there.

## Limits

- The job runs as one UID (`NEXAHOME_BACKUP_UID`, default 1001, the Actual user). A stack whose files only another UID can read will fail to back up; the fix is a decision for the first such stack ([ADR 0008](../../docs/adr/0008-backup-tool.md)).
- Tested on macOS with Colima (virtiofs). On Linux, bind-mounted directories keep their real owner, so the repository directory must be writable by `NEXAHOME_BACKUP_UID`; not tested.
- Retention is manual: with `NEXAHOME_BACKUP_DIR` and `NEXAHOME_RESTIC_PASSWORD_FILE` set, run `docker compose -f stacks/backup/compose.yaml run --rm restic forget --keep-daily 7 --keep-weekly 4 --keep-monthly 6 --prune`.
