# NexaHome

A modular, self-hosted homelab platform: local AI, development tools, storage, networking and home automation. Built to be reproducible, secure and easy to adapt to your own hardware.

**Status:** early foundation. One demo stack (`hello`) runs on a laptop. CI (secret scan and `make check`) has run once and passed; see the [session log](docs/session-log.md).

## Quick start

Needs `git`, `make`, and a Docker CLI with Compose and a running engine (on macOS the project uses [Colima](docs/adr/0004-colima-runtime.md)). `hello` is a demo that serves one static page.

```sh
make up STACK=hello       # start the demo stack and wait until healthy
make ps STACK=hello       # shows the service as healthy
curl http://127.0.0.1:8080/
make down STACK=hello
```

`make help` lists all targets.

## Your data stays yours

Each stack's `.env` and the `data/` directory are local only and gitignored. Nothing you configure is sent upstream.

## Updating

No releases yet: use `main`, and run `git pull` to update.

## Layout

- `docs/` documentation: start at the [documentation index](docs/README.md)
- `stacks/<name>/` one deployable unit each: `compose.yaml`, `.env.example`, README
- `scripts/` the checks behind `make check`

## Contributing

Pull requests are welcome from forks; there is no support promise. Developer setup is in [CONTRIBUTING.md](CONTRIBUTING.md).

## Security

See [SECURITY.md](SECURITY.md). Never commit secrets or personal data.

## Licence

[MIT](LICENSE)
