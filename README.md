# NexaHome

A modular, self-hosted homelab platform: local AI, development tools, storage, networking and home automation. Built to be reproducible, secure and easy to adapt to your own hardware.

**Status:** early foundation. One demo stack (`hello`) runs on a laptop. CI (secret scan and `make check`) has run once and passed; see the [session log](docs/session-log.md).

## Quick start

Needs `git`, `make`, Python 3 and a Docker CLI with Compose and a running engine (on macOS the project uses [Colima](docs/adr/0004-colima-runtime.md)). Optional: `uv`.

```sh
make setup                # create .venv and install the pinned dev tools
make check                # hooks on every file plus the Compose policy check
make up STACK=hello       # start the demo stack and wait until healthy
make ps STACK=hello       # shows the service as healthy
curl http://127.0.0.1:8080/
make down STACK=hello
```

`make check` ends without errors when everything passes. To remove everything: `make down`, delete `.venv`, and `colima delete` if you no longer need the runtime. `make help` lists all targets.

## Layout

- `docs/` documentation: start at the [documentation index](docs/README.md)
- `stacks/<name>/` one deployable unit each: `compose.yaml`, `.env.example`, README
- `scripts/` the checks behind `make check`
- `data/` and every `.env` are local only and gitignored

## Contributing

Pull requests are welcome from forks; there is no support promise. Read [constraints](docs/constraints.md) first and see the [branching model](docs/adr/0002-branching.md). Run `make check` before opening a pull request.

## Security

See [SECURITY.md](SECURITY.md). Never commit secrets or personal data.

## Licence

[MIT](LICENSE)
