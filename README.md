# NexaHome

A modular, self-hosted homelab platform: local AI, development tools, storage, networking and home automation. Built to be reproducible, secure and easy to adapt to your own hardware.

**Status:** early foundation. Two stacks run on a laptop: a demo (`hello`) and Actual Budget (`actual`, a local expense tracker; use dummy data until backups are proven). CI (secret scan and `make check`) has run once and passed; see the [session log](docs/session-log.md).

## Quick start

Needs `git`, `make`, and a Docker CLI with Compose and a running engine. On Linux, Docker Engine runs directly. On macOS the project uses [Colima](docs/adr/0004-colima-runtime.md); start it once per boot:

```sh
colima start --cpu 2 --memory 2 --disk 20
```

```sh
make up                   # start every stack and wait until healthy
make ps                   # shows each service as healthy
curl http://127.0.0.1:8080/        # hello, a static demo page
curl http://127.0.0.1:5006/info    # actual, an expense tracker (open it in a browser)
make down                 # stop; your data volumes are kept
```

Add `STACK=hello` or `STACK=actual` to act on one stack. The first `make up` creates each stack's `.env` from `.env.example`. `make` lists all targets.

## Your data stays yours

Each stack's `.env` and the `data/` directory are local only and gitignored. Nothing you configure is sent upstream.

## Updating

No releases yet: use `main`, and run `git pull` to update.

## Layout

- `docs/` documentation: start at the [documentation index](docs/README.md)
- `stacks/<name>/` one deployable unit each: `compose.yaml`, `.env.example`, README; `stacks/_template/` is the starting point for a new one
- `scripts/` the checks behind `make check`

## Contributing

Pull requests are welcome from forks; there is no support promise. Developer setup is in [CONTRIBUTING.md](CONTRIBUTING.md).

## Security

See [SECURITY.md](SECURITY.md). Never commit secrets or personal data.

## Licence

[MIT](LICENSE)
