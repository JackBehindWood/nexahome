# Add a stack

Version 0.1 · Last reviewed 2026-11-04

**Audience:** developers and contributors with a clone or a fork. **Admin rights needed:** no. If you installed the package and have no clone, use [Make your own stack](own-stack.md).

```sh
cp -R stacks/_template stacks/<name>   # then edit compose.yaml, .env.example, README.md
make check                             # label, project name and Compose policy
make up STACK=<name>
make ps STACK=<name>
make down STACK=<name>
```

Checklist before the pull request (the [stack proposal form](../../.github/ISSUE_TEMPLATE/stack-proposal.yml) asks for the same facts, so an idea can be agreed before the work):

0. `make check` passes (it runs `nexahome check`, the Compose policy, and the hooks).
1. `name:` is `nexahome-<name>`; the image has an exact tag and supports arm64.
2. Every named volume has `nexahome.backup: "true"` or `"false"`.
3. Ports bind to `127.0.0.1` with the host port from a variable that has a default; every variable is in `.env.example` (placeholders only; `CHANGE_ME` makes `make up` stop).
4. The README records measured RAM and disk, whether the stack must run 24/7, what is backed up and how to verify a restore. A stack with a backed-up volume is drilled once: `make down STACK=<name>`, `make backup`, `make verify STACK=<name>` must print `equal`.
5. Add an entry for `/stacks/<name>` to `.github/dependabot.yml`: ecosystem `docker-compose`, or `docker` when the stack builds from a `Dockerfile` (as `gatus` does).
6. A significant choice (for example the application itself) gets an ADR.

## What is stable

What a script, a tool or your own stack may rely on; everything else can change between releases.

- **Stack contract:** [ADR 0007](../adr/0007-stack-contract.md) and the [Compose policy](../constraints.md#compose-policy). Your stack is a folder with `compose.yaml`, `.env.example` and `README.md`.
- **`--json` output** of `doctor`, `stacks` and `update --available` carries a `schema` integer (`REPORT_SCHEMA`, `STACKS_JSON_SCHEMA`, `UPDATE_JSON_SCHEMA` in [`defaults.py`](../../src/nexahome/defaults.py)); the shape is described in [`report.py`](../../src/nexahome/report.py) and `nexahome <command> --help`. Check the integer and stop on one you do not know. `doctor` check ids are added, never renamed.
- **`nexahome.toml`** has a schema integer (`INSTANCE_SCHEMA`); a file with a newer one is refused, never guessed ([ADR 0020](../adr/0020-instance-install-and-release-model.md)). `nexahome config` is the way to edit it.
- **Exit codes** are the table in the [README](../../README.md#the-nexahome-command).
- Not written down yet: a rule for when a schema integer rises. Until there is one, treat a changed integer as a breaking change.

## Give a web app a name, a sign-in and a tile (five steps)

Stacks without a web UI skip this. `<domain>` and `<port>` are `NEXAHOME_DOMAIN` and `EDGE_PORT` (equal in every stack's `.env`). Replace `<name>` and `<app-port>`.

1. **Network and alias.** In the app's `compose.yaml`, join the external network `nexahome-edge` (service `networks: [edge]`; top level `edge: {external: true, name: nexahome-edge}`). In `stacks/edge/compose.yaml`, add the alias `<name>.${NEXAHOME_DOMAIN:-nexahome.localhost}` under the edge service's network aliases (the alias sits on the edge, not on the app). An app that is already running must be recreated to join the network: `make up STACK=<name>`.
2. **Route.** In `stacks/edge/Caddyfile`, add a block: `http://<name>.{$NEXAHOME_DOMAIN}:{$EDGE_PORT} { import hardening` then `reverse_proxy <service>:<app-port> }`. Apply it with `make up STACK=edge` (the new alias makes Compose recreate the edge; a Caddyfile-only change needs `docker compose restart` in `stacks/edge`).
3. **Sign-in.** If the app has accounts: use OIDC. Register a client in the provider (see [identity README](../../stacks/identity/README.md)), put the client id and secret in the app's `.env` and the variable names in its `.env.example`, and restrict the client to groups. If the app has no accounts, say so in its README and keep it reachable only by name or on loopback.
4. **Tile.** Add one entry under `Apps` (or `Platform` for infrastructure) in `stacks/portal/config/services.yaml` with `href` and `siteMonitor` set to `http://<name>.{{HOMEPAGE_VAR_DOMAIN}}:{{HOMEPAGE_VAR_PORT}}/`. The portal re-reads the file on every page load; no restart (measured).
5. **Health target.** Add the same URL as a target in `stacks/gatus/config/config.yaml` and restart the tool with `docker compose restart` in `stacks/gatus`. `make smoke` lists a tile without a target.

Check with `make smoke`: it lists any alias without a Caddyfile block or tile (or the reverse) and every tile's dot. `make check` does not catch a missing tile or alias; that check is deferred until the first miss.

Rules: [Compose policy](../constraints.md#compose-policy). Contract: [ADR 0007](../adr/0007-stack-contract.md).

Changelog: 0.1 (2026-11-04): checklist step 0 and a "What is stable" section (contributor starter pack); 0.1 (2026-11-04): audience line points runners to the own-stack runbook (Goal 3); 0.1 (2026-11-02): version header and changelog added; five steps for a web app (the health target was hidden in step 4); Dependabot ecosystem note (PK2).
