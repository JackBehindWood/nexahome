# NexaHome

A modular, self-hosted homelab platform: local AI, development tools, storage, networking and home automation. Built to be reproducible, secure and easy to adapt to your own hardware.

**Status:** early foundation. Seven stacks run on a laptop: a demo (`hello`), Actual Budget (`actual`, a local expense tracker; use dummy data until backups are proven), `backup`, `edge`, `identity`, `portal` and `gatus`. CI (secret scan and `make check`) runs on every push and pull request to `main` and `dev`; see the [session log](docs/session-log.md).

## Quick start

Needs `git`, `make`, and a Docker CLI with Compose and a running engine. On Linux, Docker Engine runs directly. On macOS the project uses [Colima](docs/adr/0004-colima-runtime.md); start it once per boot. On Windows, use WSL2: it counts as Linux, best effort and not tested in CI ([ADR 0019](docs/adr/0019-platform-support-and-ci-matrix.md)). Running stacks needs no Python; Python 3.13 or newer (or `uv`, which fetches it) is only for [contributing](CONTRIBUTING.md):

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

A small command-line tool that checks your machine and prepares a checkout. `make` still starts, stops and backs up everything; `nexahome` starts no container. It needs Python 3.13 or newer (or `uv`, which fetches it). From a clone:

```sh
make setup                  # once: creates .venv and installs the tool into it
. .venv/bin/activate        # once per terminal; then plain `nexahome` works
nexahome doctor             # diagnose this machine; every problem ends in one command to run
nexahome env                # create each stack's .env and generate its secrets (add --dry-run to look first)
nexahome stacks             # which stacks exist, which this host runs, whether they are running
nexahome status             # health of the stacks and how recent the backup is
nexahome check              # the Compose policy over the stacks
nexahome update --available # is a newer release out? (there is none yet)
```

`make setup` prepares the tool itself (the virtual environment); `nexahome env` prepares the stacks (their `.env` files). `nexahome --help` lists every command and `nexahome <command> --help` its options. Without activating the environment, call `.venv/bin/nexahome`. Run it from inside the checkout, or point `NEXAHOME_HOME` at the checkout. `doctor`, `stacks` and `update --available` also take `--json` for scripts (schema 1, described in `src/nexahome/report.py`). It is not on PyPI and has no release yet; `make test` runs its tests ([CONTRIBUTING](CONTRIBUTING.md#the-nexahome-package)).

Exit codes, the same for every command:

| Code | Meaning |
| :-- | :-- |
| 0 | done, nothing to fix |
| 1 | `check` found a policy problem |
| 2 | wrong usage (unknown command or option) |
| 3 | this host is not ready (for example Docker is missing or stopped, no stacks to check, a `.env` still needs a value); the message ends in the command that fixes it |
| 130 | interrupted (Ctrl-C) |
| 141 | the reader went away, for example `nexahome stacks \| head` |

`make check` still runs the original scripts, which exit 0 or 1; `nexahome check` exits 3 where they would exit 0 or 1 for "no stacks" or "Docker CLI missing" (the hooks switch to it in PK5).

## Your data stays yours

Each stack's `.env` and the `data/` directory are local only and gitignored. Nothing you configure is sent upstream.

## Back up, restore, update

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
- `scripts/` the checks behind `make check`, and the backup, smoke, deploy and setup scripts

## Contributing

Pull requests are welcome from forks; there is no support promise. Developer setup is in [CONTRIBUTING.md](CONTRIBUTING.md).

## Security

See [SECURITY.md](SECURITY.md). Never commit secrets or personal data.

## Licence

[MIT](LICENSE)
