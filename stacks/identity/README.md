# identity

[Pocket ID](https://pocket-id.org): passkey-only OIDC provider and the one sign-in page (My Apps) for NexaHome apps ([ADR 0010](../../docs/adr/0010-identity-provider.md), Proposed). No published port; open it through the edge at `http://id.<NEXAHOME_DOMAIN>:<EDGE_PORT>` (default `http://id.nexahome.localhost:8088`). Needs the `edge` stack.

```sh
make up STACK=edge
make up STACK=identity   # first start generates ENCRYPTION_KEY in .env (not shown)
make down STACK=identity # the data volume is kept
```

| Item | Value |
| :--- | :--- |
| RAM (measured, idle, 2026-10-22) | 16 MiB (limit 128 MiB) |
| Disk (measured) | image 110 MB; data volume small (database, uploads, a background image of about 0.5 MB) |
| Must run 24/7? | no |
| Backed up | volume `data` (database, uploaded images), labelled `nexahome.backup: "true"`; `.env` with `ENCRYPTION_KEY` is saved by `make backup` |
| Verify after a restore | `make down STACK=identity`, `make verify STACK=identity` prints `equal`; after a restore `make up`, sign in with a registered passkey and see the same users and clients (drilled 2026-10-23: [ADR 0010](../../docs/adr/0010-identity-provider.md)) |
| Clients | `actual` ([stack](../actual/README.md)) |

## First run

1. Open `/setup`, create the admin account, add a passkey. A second passkey needs a different authenticator (phone or security key): the same iCloud Keychain counts as one and is refused.
2. Copy `ENCRYPTION_KEY` from `.env` into your password manager. A restored database is unusable without it.
3. Groups: `admin`, `users`, `agents` (reserved, never admin, no client access). Normal users: create the account, add it to `users`, send a one-time sign-in link, and have them add a passkey right away: an account without one cannot finish an app sign-in (blank page, measured). Check with `make open`.

## Register an app (client)

By hand in the UI (Administration, OIDC Clients). No API key is set in this stack.

| Field | Value |
| :--- | :--- |
| Name | the app's name |
| Callback URL | `http://<app>.<NEXAHOME_DOMAIN>:<EDGE_PORT>/openid/callback` (check the app's docs) |
| Launch URL | `http://<app>.<NEXAHOME_DOMAIN>:<EDGE_PORT>/` (shows in My Apps) |
| Group restricted | on, with `admin` and `users` allowed. Without the switch the group list does nothing |
| Secret | generate once, put it in the app's `.env` |

## Recovery

Step by step: [identity-recovery runbook](../../docs/runbooks/identity-recovery.md) (followed once on 2026-10-23). The host-side one-time link is admin power: host access only. Sessions last one day (Administration, Application Configuration). Refusals are not written to the audit log (v2.18); only successes are.

Runs as uid 65532 with a read-only root. The image has no `/app/data`, so the volume is mounted at the image's non-root home directory. Telemetry and update checks are off. Dummy data only.
