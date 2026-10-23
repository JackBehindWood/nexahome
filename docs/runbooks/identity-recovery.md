# Recover access to identity and Actual

**Audience:** the person who runs NexaHome. **Admin rights needed:** yes: shell access to the host that runs the stacks (the commands below are admin power; a one-time link signs in as that user, so treat it like a password and never paste it into chat or a ticket). Needs the container runtime running ([README](../../README.md)). Design: [ADR 0010](../adr/0010-identity-provider.md), [ADR 0011](../adr/0011-edge-and-local-hostnames.md).

## Symptoms and where to go

| Symptom | Section |
| :--- | :--- |
| Every passkey of the admin is lost or unusable | [A](#a-admin-passkey-lost) |
| A normal user lost their passkey, or has none yet | [A](#a-admin-passkey-lost) (same command, that user's name) |
| Actual asks for OpenID and the provider is down or unusable | [C](#c-actual-sign-in-without-the-provider) |
| Server password of Actual lost | [C](#c-actual-sign-in-without-the-provider) |
| Restored identity database will not open | [D](#d-lost-encryption-key) |

Everything runs on the host and needs no working login. Nothing here needs `sudo`, root containers or a published port.

## A. Admin passkey lost

1. Start the edge and identity stacks: `make up STACK=edge`, then `make up STACK=identity`.
2. Issue a one-time sign-in link (valid one hour, single use) and open it in a normal browser window:

   ```sh
   cd stacks/identity
   docker compose exec identity /app/pocket-id one-time-access-token <username> | grep -Eo 'https?://[^ ]+'
   ```

   Open the printed address. On macOS, `| xargs open` after the `grep` opens it without showing it. If the page says the token is invalid, it was used already (a reload counts): issue a new one.
3. You are signed in as that user. Open the profile menu, **My account**, **Passkeys**. On a new device, add the new passkey, then delete the lost one. If the new passkey comes from the same authenticator as the lost one (the same Keychain, measured), adding is refused as a duplicate: delete the old one first, then add. The link keeps working, so a failed add costs nothing: issue a new link.
4. Sign out, then sign in again with the picker entry for the account. A one-time link alone does not complete an app sign-in: the provider shows a blank interaction page for an account without a passkey.
5. Open My Apps and launch Actual to confirm the whole path.

A passkey is bound to the hostname. If `NEXAHOME_DOMAIN` changed, every account needs this procedure once.

## B. Check after any recovery

- `make ps` shows edge, identity and actual healthy.
- Administration, Audit Log shows the sign-ins you made.
- Nothing in Git or in the terminal history contains the link.

## C. Actual sign-in without the provider

Actual keeps its login choice in its own database, not in `.env`: removing the OpenID variables does **not** switch it back (measured). The password login is still stored (inactive) and can be chosen on the login page ("switch login method"), if you know the server password. Run these on the host, in `stacks/actual`:

| Goal | Command | Effect |
| :--- | :--- | :--- |
| Forgot the server password | `docker compose exec -it actual node src/scripts/reset-password.js` | Prompts for a new password (hidden). Replaces only the password hash; OpenID stays active, users and budgets untouched. Works with the provider down |
| Leave OpenID for good | `docker compose exec -it actual node src/scripts/disable-openid.js` | Needs the server password. Deletes the OpenID setting, all sessions and every user except the owner row, with their file access. Budget files stay |
| Turn OpenID back on | `docker compose exec -it actual node src/scripts/enable-openid.js` | Needs the `ACTUAL_OPENID_*` variables set |

Existing Actual sessions never expire by default and ignore group changes in the provider; ending them means the commands above or `ACTUAL_TOKEN_EXPIRATION`. The server password is not in `.env`: keep it in your password manager.

## D. Lost encryption key

`ENCRYPTION_KEY` in `stacks/identity/.env` encrypts the provider's database. Without it a restored database is unusable and the provider must be set up again (new first admin, groups, users, clients, new client secrets in each app). Keep the key with the restic password in a password manager ([restore runbook](restore.md)).

## Evidence

Drill of 2026-10-23 (laptop, Safari, one authenticator, admin passkey treated as lost), from the provider's audit log: `TOKEN_SIGN_IN` (link), add refused (same Keychain), `PASSKEY_REMOVED`, `PASSKEY_ADDED` three seconds later, `SIGN_IN` with the new passkey; then Actual opened through My Apps. Section A took about three minutes including the browser steps. Findings that changed the text: the command's last line is not only the address (use `grep`), and an account without a passkey cannot finish an app sign-in: the one-time link signs in to the provider only. Sections C and D were read from the Actual source and the ADR; the password reset (C) was run once and kept every budget; `disable-openid` and `enable-openid` were not run. Not verified: a second authenticator, Chrome, Firefox, Linux.
