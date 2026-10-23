# actual

[Actual Budget](https://actualbudget.org): a local-first expense and budget tracker (MIT licence, SQLite, one container). It is the first stateful stack, the subject of the backup drill ([ADR 0009](../../docs/adr/0009-first-app-actual-budget.md)) and the first client of the identity provider ([ADR 0010](../../docs/adr/0010-identity-provider.md), Proposed). Use dummy data: the restore drill passed on 2026-10-21 with it, but the repository is on the same disk. It is the drill subject only; the owner plans an own expense app later, so this stack can be removed once another stateful stack exists.

```sh
make up STACK=actual      # start and wait until healthy
make open STACK=actual    # open http://actual.<NEXAHOME_DOMAIN>:<EDGE_PORT>/ in the browser
curl http://127.0.0.1:5006/info
make down STACK=actual    # the data volume is kept
```

Without single sign-on, open `http://127.0.0.1:5006/` and set a password on first use (stored in the volume, not in `.env`). The port is `ACTUAL_PORT` (see `.env.example`). With single sign-on the same page stays reachable on that port, and the named address goes through the edge.

| Item | Value |
| :--- | :--- |
| RAM (measured, idle, 2026-10-23, single sign-on on) | about 129 MiB (was about 130 MiB without) |
| Disk (measured) | image 331 MB; data volume about 70 KB when empty |
| Must run 24/7? | no |
| Backed up | volume `data` (`/data`: `server-files/account.sqlite`, `user-files/`), labelled `nexahome.backup: "true"`; `.env` is saved by `make backup` |
| Verify after a restore | `make restore STACK=actual TARGET=check`, start it on another port ([runbook](../../docs/runbooks/restore.md)), sign in and open a budget file you know; the owner's drill used `drill-budget-1` with one known transaction |

Runs as uid 1001 (the image's own `actual` user) with a read-only root filesystem and a tmpfs `/tmp`. The image ships no health check and runs as root by default; this stack overrides both. It joins the network `nexahome-edge`; the edge routes `actual.<NEXAHOME_DOMAIN>` to it.

## Sign in with SSO

Needs the `edge` and `identity` stacks and an `actual` client in the provider ([field table](../identity/README.md#register-an-app-client)).

1. In the provider, generate a secret for the client and put it in `stacks/actual/.env` as `ACTUAL_OPENID_CLIENT_SECRET` (never in chat or Git). Run `make up STACK=actual`.
2. Open Actual by its named address. On an instance that already has a password, Actual shows **Start using OpenID** once: enter the current server password and click it. Actual then signs everyone out.
3. The first user who signs in with OpenID becomes the server owner and cannot be changed in the UI: make that the provider's `admin`.
4. After that, My Apps lists Actual for members of `admin` and `users` only, and the launch link opens Actual signed in.

What was measured (2026-10-23, Actual 26.10.0):

- **Where the choice lives.** The `ACTUAL_OPENID_*` variables only prefill that one-time screen. The active login method, and a copy of the client secret, are stored in Actual's database (the volume). Emptying the variables does not switch OpenID off; a rotated secret must also be given to Actual again, as the admin in Actual's authentication settings (the review OpenID configuration screen; `enable-openid.js` does nothing while OpenID is active). End to end: see the session log for whether this was verified.
- **Second user.** Actual matches the provider's `preferred_username` (then `login`, `email`, `id`, `sub`) to its own user name. `ACTUAL_USER_CREATION_MODE=login` (set here) creates the Actual user at first sign-in with the Basic role, so group membership in the provider decides who gets in; `manual` makes the owner add each user first. The existing budget file has the server as owner: share it with a user in Actual (file menu, user access) or they see no files.
- **Passkey needed.** An account without a passkey cannot finish an app sign-in; the provider shows a blank page. Add a passkey to every account.
- **Sessions.** Actual keeps its own login for `ACTUAL_TOKEN_EXPIRATION` seconds (set to one day; Actual's default is never) and ignores later group changes in the provider. Removing someone from `users` blocks new sign-ins only; an existing Actual session lasts until it expires.
- **Password fallback.** The password row stays in Actual's database (inactive). On the login page, switch the login method to password. To reset a lost password or leave OpenID, see the [recovery runbook](../../docs/runbooks/identity-recovery.md#c-actual-sign-in-without-the-provider).
- **Provider or edge down.** Existing sessions keep working (Actual checks them in its own database). A new OpenID login fails with `openid-setup-failed`. Actual started with both down logs `configuration-error` but stays healthy (no crash loop, 0 restarts) and accepts logins again once they are back, without a restart. The password login works throughout.

| Message in the browser | Cause |
| :--- | :--- |
| "You are not allowed to access this service" (provider page) | the account is in no group allowed for the client |
| Blank or black provider page after the sign-in button | the account has no passkey |
| "Something went wrong" in Actual | the provider refused or sent no code; the Actual log shows `openid-grant-failed` or no callback. Check the provider's audit log |
| Actual goes straight in with the wrong user | the browser still holds a login token; sign out in Actual or clear the site data for the Actual address. Private windows can break Actual's storage |
