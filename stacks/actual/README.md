# actual

[Actual Budget](https://actualbudget.org): a local-first expense and budget tracker (MIT licence, SQLite, one container). It is the first stateful stack and the subject of the backup drill ([ADR 0009](../../docs/adr/0009-first-app-actual-budget.md)). Use dummy data until the restore drill has passed.

```sh
make up STACK=actual      # start and wait until healthy
curl http://127.0.0.1:5006/info
make down STACK=actual    # the data volume is kept
```

Open `http://127.0.0.1:5006/` and set a password on first use (it is stored in the volume, not in `.env`). The port is `ACTUAL_PORT` (see `.env.example`).

| Item | Value |
| :--- | :--- |
| RAM (measured, idle, 2026-10-21) | about 130 MiB |
| Disk (measured) | image about 70 MB; data volume about 70 KB when empty |
| Must run 24/7? | no |
| Backed up | volume `data` (`/data`: `server-files/account.sqlite`, `user-files/`), labelled `nexahome.backup: "true"` |
| Verify after a restore | sign in and open a known budget file |

Runs as uid 1001 (the image's own `actual` user) with a read-only root filesystem and a tmpfs `/tmp`. The image ships no health check and runs as root by default; this stack overrides both.
