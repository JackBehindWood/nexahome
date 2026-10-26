# Add a stack

**Audience:** developers and contributors. **Admin rights needed:** no.

```sh
cp -R stacks/_template stacks/<name>   # then edit compose.yaml, .env.example, README.md
make check                             # label, project name and Compose policy
make up STACK=<name>
make ps STACK=<name>
make down STACK=<name>
```

Checklist before the pull request:

1. `name:` is `nexahome-<name>`; the image has an exact tag and supports arm64.
2. Every named volume has `nexahome.backup: "true"` or `"false"`.
3. Ports bind to `127.0.0.1` with the host port from a variable that has a default; every variable is in `.env.example` (placeholders only; `CHANGE_ME` makes `make up` stop).
4. The README records measured RAM and disk, whether the stack must run 24/7, what is backed up and how to verify a restore. A stack with a backed-up volume is drilled once: `make down STACK=<name>`, `make backup`, `make verify STACK=<name>` must print `equal`.
5. Add a `docker-compose` entry for `/stacks/<name>` to `.github/dependabot.yml`.
6. A significant choice (for example the application itself) gets an ADR.

## Give a web app a name, a sign-in and a tile (four steps)

Stacks without a web UI skip this. `<domain>` and `<port>` are `NEXAHOME_DOMAIN` and `EDGE_PORT` (equal in every stack's `.env`). Replace `<name>` and `<app-port>`.

1. **Network and alias.** In the app's `compose.yaml`, join the external network `nexahome-edge` (service `networks: [edge]`; top level `edge: {external: true, name: nexahome-edge}`). In `stacks/edge/compose.yaml`, add the alias `<name>.${NEXAHOME_DOMAIN:-nexahome.localhost}` under the edge service's network aliases (the alias sits on the edge, not on the app). An app that is already running must be recreated to join the network: `make up STACK=<name>`.
2. **Route.** In `stacks/edge/Caddyfile`, add a block: `http://<name>.{$NEXAHOME_DOMAIN}:{$EDGE_PORT} { import hardening` then `reverse_proxy <service>:<app-port> }`. Apply it with `make up STACK=edge` (the new alias makes Compose recreate the edge; a Caddyfile-only change needs `docker compose restart` in `stacks/edge`).
3. **Sign-in.** If the app has accounts: use OIDC. Register a client in the provider (see [identity README](../../stacks/identity/README.md)), put the client id and secret in the app's `.env` and the variable names in its `.env.example`, and restrict the client to groups. If the app has no accounts, say so in its README and keep it reachable only by name or on loopback.
4. **Tile.** Add one entry under `Apps` (or `Platform` for infrastructure) in `stacks/portal/config/services.yaml` with `href` and `siteMonitor` set to `http://<name>.{{HOMEPAGE_VAR_DOMAIN}}:{{HOMEPAGE_VAR_PORT}}/`. The portal re-reads the file on every page load; no restart (measured). Also add the URL as a target in `stacks/gatus/config/config.yaml` (restart the tool with `docker compose restart` in `stacks/gatus`); `make smoke` lists a tile without a target.

Check with `make smoke`: it lists any alias without a Caddyfile block or tile (or the reverse) and every tile's dot. `make check` does not catch a missing tile or alias; that check is deferred until the first miss.

Rules: [Compose policy](../constraints.md#compose-policy). Contract: [ADR 0007](../adr/0007-stack-contract.md).
