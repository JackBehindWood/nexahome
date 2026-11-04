# Make your own stack

Version 0.1 · Last reviewed 2026-11-04

**Audience:** someone who installed the `nexahome` package and ran `nexahome init` (no clone, no `make`). **Admin rights needed:** no. To add a stack to the repository itself, use [Add a stack](add-a-stack.md) instead.

```sh
cd ~/nexahome                          # the folder `nexahome init` made
nexahome stacks new notes              # copies the template to stacks/notes and enables it
nexahome check                         # the Compose policy; a failure names the file to edit
nexahome env                           # creates stacks/notes/.env and generates secrets
docker compose -f stacks/notes/compose.yaml up -d --wait   # `nexahome up` will replace this line
```

`new` prints these lines for your stack, with its port. The generated stack runs as it is (a tiny web server answering on `127.0.0.1`), so you can see it work before you change anything. Then replace the image and settings in `stacks/notes/compose.yaml` with your service and run `nexahome check` again.

## What you get

`stacks/<name>/` holds `compose.yaml`, `.env.example` and `README.md`, renamed for your stack (project `nexahome-<name>`, variable `<NAME>_PORT`, the smallest free port from 8081 up). `nexahome stacks` lists it with owner `user`; the stacks that came with the package say `package`. The rules your `compose.yaml` must meet are in the [Compose policy](../constraints.md#compose-policy) and [ADR 0007](../adr/0007-stack-contract.md); this page does not repeat them.

## Rules of the road

- **Yours and the package's stay apart.** `update` changes the tool, never your stacks. Do not edit the package's stacks; a name that belongs to the package (`hello`, `edge`, ...) is refused.
- **Volumes need a label.** Every named volume carries `nexahome.backup: "true"` (back it up) or `"false"` (disposable); `nexahome check` fails without it.
- **Secrets.** `.env.example` holds placeholders only. A value `CHANGE_ME` stops `nexahome env` until you set it; `GENERATE` is filled with a random secret.
- **No name, sign-in or tile on the portal.** Wiring an app into the edge, the portal and the health view means editing files the package owns, so it is not supported for your own stacks. Open the app on its loopback address instead. A fork can do it ([Add a stack](add-a-stack.md), the five steps).
- **Backups.** The backup and restore tools are Makefile targets in a clone and are not available to an instance yet. Your stack's `.env` and data exist only in this folder: copy them yourself until the package can back them up.

## Remove it

```sh
nexahome stacks remove notes           # lists every file that goes (including .env), then asks
```

It refuses a running stack (stop it with the `docker compose ... down` line it prints), a package stack, and a folder that contains a link. It never deletes Docker volumes; it prints the command that lists them, so data you want gone is a choice you make. `--yes` skips the question.

## Not checked yet

Starting, stopping and removing a stack on a running engine, Linux, and the time a first-time reader needs. See [the session log](../session-log.md) for what was run.

Changelog: 0.1 (2026-11-04): first version (Goal 3).
