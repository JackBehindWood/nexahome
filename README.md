# NexaHome

A modular, self-hosted homelab platform: local AI, development tools, storage, networking and home automation. Built to be reproducible, secure and easy to adapt to your own hardware.

**Status:** early foundation. The stacks run on a laptop: a demo (`hello`), Actual Budget (`actual`, a local expense tracker; use dummy data until backups are proven), `backup`, `edge`, `identity`, `portal` and `gatus`. CI runs on every push and pull request; the latest result is in the [session log](docs/session-log.md).

## Quick start

Two ways in. Both need a Docker CLI with Compose and a running engine: on Linux, Docker Engine runs directly; on macOS the project uses [Colima](docs/adr/0004-colima-runtime.md), started once per boot (`colima start --cpu 2 --memory 2 --disk 20`); on Windows use WSL2, which counts as Linux, best effort and not tested in CI ([ADR 0019](docs/adr/0019-platform-support-and-ci-matrix.md)).

### Run NexaHome as shipped (needs the wheel)

For anyone who wants the stacks as they are. You need Python 3.13 or newer, or [`uv`](https://docs.astral.sh/uv/), which fetches it. There is no release yet, so the wheel comes from a clone (`uv build --wheel`, then `dist/`) until the first tag; replace the file name below with yours.

```sh
uv tool install ./nexahome-<version>-py3-none-any.whl   # puts `nexahome` on your PATH, in its own environment
nexahome init                    # makes ~/nexahome from the stacks inside the package; it never overwrites
cd ~/nexahome
nexahome doctor                  # every problem ends in one command to run
docker network inspect nexahome-edge >/dev/null 2>&1 || docker network create nexahome-edge
docker compose -f stacks/hello/compose.yaml up -d --wait
curl http://127.0.0.1:8080/      # hello, a static demo page
docker compose -f stacks/hello/compose.yaml down
```

Without `uv`: `python3.13 -m venv venv && venv/bin/pip install ./nexahome-<version>-py3-none-any.whl`, then call `venv/bin/nexahome`. `nexahome init DIR` makes the folder somewhere else; keep it under your home directory, because Colima mounts only that.

To run more stacks, list them and let the command prepare their `.env` files (some need values from you first; it says which), then start each one as above:

```sh
nexahome config set stacks hello actual   # the stacks this folder runs, kept in nexahome.toml
nexahome env                              # creates each .env, generates secrets (never shown), then runs doctor
docker compose -f stacks/actual/compose.yaml up -d --wait
```

The `docker compose` lines are a manual form of `make up` and `make down` (which need a clone) without its `.env` handling; a `nexahome up` will replace them. Backup, restore, smoke checks and deploy are also still Makefile targets, so they need a clone for now. The stacks in `~/nexahome/stacks` belong to the package: do not edit them. Your changes go in each stack's `.env` (a `compose.override.yaml` is read by the manual commands above only if you add `-f stacks/<name>/compose.override.yaml` after the first `-f`, because they name the file with `-f`; `nexahome check` reads it for you). Anything that edits the three files that list every named app (the edge `Caddyfile`, the portal `services.yaml`, the Gatus targets) means forking the repository, the second way in.

### Fork it, contribute, or run the full tooling (clone)

Needs `git` and `make` too. Running stacks needs no Python; Python 3.13 or newer (or `uv`) is only for [contributing](CONTRIBUTING.md) and the `nexahome` command below.

```sh
colima start --cpu 2 --memory 2 --disk 20
```

```sh
make up                   # start every stack and wait until healthy
make ps                   # shows each service as healthy
make smoke                # read-only checks of everything that runs
make verify               # after make down and make backup: prove each backup restores (copy compared, then removed)
make portal               # start the edge and the portal, open the status board (tiles and health dots)
curl http://127.0.0.1:8080/        # hello, a static demo page
curl http://127.0.0.1:5006/info    # actual, an expense tracker (open it in a browser)
make down                 # stop; your data volumes are kept
```

Add `STACK=hello` or `STACK=actual` to act on one stack. The first `make up` creates each stack's `.env` from `.env.example`. `make` lists all targets.

## The `nexahome` command

A small command-line tool that checks your machine and prepares a folder of stacks: an instance made by `nexahome init`, or a clone. `make` still starts, stops and backs up everything in a clone; `nexahome` starts no container. It needs Python 3.13 or newer (or `uv`, which fetches it). From a clone:

```sh
make setup                  # once: creates .venv and installs the tool into it
. .venv/bin/activate        # once per terminal; then plain `nexahome` works
nexahome doctor             # diagnose this machine; every problem ends in one command to run
nexahome env                # create each stack's .env and generate its secrets (add --dry-run to look first)
nexahome init [DIR]         # make a new instance from the stacks inside the package (see Quick start)
nexahome config             # show nexahome.toml; `config set stacks NAME...` chooses the stacks an instance runs
nexahome stacks             # which stacks exist, which this host runs, whether they are running
nexahome status             # health of the stacks and how recent the backup is
nexahome check              # the Compose policy over the stacks
nexahome update --available # is a newer release out? (there is none yet)
```

`make setup` prepares the tool itself (the virtual environment); `nexahome env` prepares the stacks (their `.env` files). `nexahome update` needs `NEXAHOME_UPDATE_URL` until the first release. `nexahome --help` lists every command and `nexahome <command> --help` its options. Without activating the environment, call `.venv/bin/nexahome`. Which folder it works on: `--home DIR` (given before the command), else `$NEXAHOME_HOME`, else the nearest folder above you that holds `nexahome.toml` (or, in a clone, `stacks/` and a Makefile), else `~/nexahome` when that holds a `nexahome.toml`. `doctor`, `stacks` and `update --available` also take `--json` for scripts (schema 1, described in `src/nexahome/report.py`). It is not on PyPI and has no release yet; `make test` runs its tests ([CONTRIBUTING](CONTRIBUTING.md#the-nexahome-package)).

Exit codes, the same for every command:

| Code | Meaning |
| :-- | :-- |
| 0 | done, nothing to fix |
| 1 | `check` found a policy problem |
| 2 | wrong usage (unknown command or option) |
| 3 | this host is not ready (for example Docker is missing or stopped, no stacks to check, a `.env` still needs a value); the message ends in the command that fixes it |
| 130 | interrupted (Ctrl-C) |
| 141 | the reader went away, for example `nexahome stacks \| head` |

`make check` runs `nexahome check` for the Compose policy. The script it replaced exited 0 for "no stacks" and 1 for "Docker CLI missing"; both now exit 3, with a message that ends in the fixing command.

## Your data stays yours

Each stack's `.env` and the `data/` directory are local only and gitignored. Nothing you configure is sent upstream.

## Back up, restore, update

The Makefile targets below need a clone; an installed instance has no backup command yet.

```sh
make backup-init          # once: creates the encrypted repository and a password file
make backup               # saves every stack's data (stops each for a few seconds)
make restore STACK=actual # restores into new volumes; never overwrites
make backup && git pull && make up    # update (no releases yet: use main)
```

Once releases exist, `nexahome update` will update the tool itself (it checks for a newer release, asks, and verifies the download); the stacks still update with git.

Save a copy of the password file (`.config/restic-password`) somewhere other than this laptop; without it the backups are unreadable. The backup sits on the same disk by default, so it is a drill, not protection. Test a restore before you trust it: [restore runbook](docs/runbooks/restore.md), which also covers going back after a failed update.

## Layout

- `docs/` documentation: start at the [documentation index](docs/README.md)
- `stacks/<name>/` one deployable unit each: `compose.yaml`, `.env.example`, README; `stacks/_template/` is the starting point for a new one
- `src/nexahome/` and `tests/` the `nexahome` command and its tests
- `scripts/` the backup, smoke, deploy and setup scripts (the checks behind `make check` live in the `nexahome` package)

How the general design differs from the owner's reference deployment: [architecture](docs/architecture.md#general-design-and-the-reference-deployment).

## Contributing

Pull requests are welcome from forks; there is no support promise. Developer setup is in [CONTRIBUTING.md](CONTRIBUTING.md).

## Security

See [SECURITY.md](SECURITY.md). Never commit secrets or personal data.

## Licence

[MIT](LICENSE)
