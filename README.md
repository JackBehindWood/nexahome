# NexaHome

A modular, self-hosted homelab platform: local AI, development tools, storage, networking, home automation, and personal applications. Built to be reproducible, secure, and easy to adapt to your own hardware.

**Status:** early foundation. Documentation and guardrails first; no services yet.

## Principles

* Smallest design that works; Docker Compose, no Kubernetes.
* Platform-independent (macOS and Linux) wherever possible.
* Code, configuration, secrets, and persistent data are kept separate.
* Nothing secret or personal is ever committed.

## Documentation

* [Project overview and decisions](docs/project.md)
* [Architecture](docs/architecture.md)
* [Constraints and security](docs/constraints.md)
* [Observability](docs/observability.md)
* [Roadmap](docs/roadmap.md) and [session log](docs/session-log.md)
* [Architecture decision records](docs/adr/)

## License

[MIT](LICENSE)
