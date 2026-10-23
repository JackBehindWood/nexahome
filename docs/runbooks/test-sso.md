# Test sign-in (SSO)

**Audience:** the person who runs NexaHome. **Admin rights needed:** yes (a provider admin account and host access). Run it after any change to the identity or Actual image tag, a restore, or before something is exposed beyond loopback. Design: [ADR 0010](../adr/0010-identity-provider.md).

## Setup (once)

- One Safari profile per test account (a normal window, not a private one: private windows break Actual). Each account needs its own passkey; a one-time link only signs in to the provider.
- Accounts (names are examples): `admin` in group `admin`; `user` in `users`; `agentx` in `agents` without a passkey; `outsider`, a permanent account in no group.
- `make up`, then `make smoke WAIT=60` must pass first.

## Matrix

| Account | Does | Expected | Evidence |
| :-- | :-- | :-- | :-- |
| admin | My Apps, then Actual | Signs in; becomes Actual's owner | Provider log: `webauthn/login/finish` 200, then `/authorize` 303, `/api/oidc/token` 200, `/api/oidc/userinfo` 200 |
| user | My Apps, then Actual | Signs in as a Basic user | Same four lines |
| agentx | My Apps | No app tile; an app sign-in cannot finish | No `/api/oidc/token`; the page stays blank |
| outsider | Open Actual, choose OpenID | "You are not allowed to access this service" | No `/api/oidc/token`; nothing in Actual's log for the user |
| any | `make smoke VERBOSE=1` after each step | `smoke: all checks passed` | Output pasted into the session log |

Read the provider log with `(cd stacks/identity && docker compose logs --since 10m identity)`; never paste a link or token into chat. Refusals are not in the provider's audit log (only successes), so the evidence for a refusal is the missing token call.

## After a restore

Run the first two rows. Actual keeps sessions for a day (`ACTUAL_TOKEN_EXPIRATION`), so sign out of Actual first, otherwise it opens without asking the provider and proves nothing.
