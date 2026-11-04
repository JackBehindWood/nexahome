"""Docker Compose: read-only questions to `docker compose`, and the arguments that name a stack's files."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nexahome.defaults import COMPOSE_CONFIG_TIMEOUT, DOCKER_TIMEOUT

if TYPE_CHECKING:
    from pathlib import Path

    from nexahome.context import Context
    from nexahome.runner import Runner, RunResult


def file_argv(compose: Path, env_example: Path | None = None) -> list[str]:
    """`docker compose -f FILE`, then the stack's `compose.override.yaml` when it exists (`docker compose` run in the stack
    folder reads it, so a check that skipped it would approve what does not run), plus `--env-file` when the stack's
    `.env.example` should supply the variables."""
    argv = ["docker", "compose", "-f", str(compose)]
    override = compose.with_name("compose.override.yaml")
    if override.is_file():
        argv += ["-f", str(override)]
    if env_example is not None:
        argv += ["--env-file", str(env_example)]
    return argv


def plugin_version(ctx: Context, *, timeout: float = DOCKER_TIMEOUT) -> RunResult:
    """`docker compose version`: succeeds when the Compose plugin is installed."""
    return ctx.runner.run(["docker", "compose", "version"], timeout=timeout)


def stack_state(ctx: Context, compose: Path) -> str:
    """"running", "stopped", or "unknown" when Docker cannot answer."""
    result = ctx.runner.run([*file_argv(compose), "ps", "--status", "running", "-q"], timeout=DOCKER_TIMEOUT)
    if not result.ok:
        return "unknown"
    return "running" if result.stdout.strip() else "stopped"


def ps(ctx: Context, compose: Path) -> RunResult:
    return ctx.runner.run([*file_argv(compose), "ps"], timeout=DOCKER_TIMEOUT)


def logs_argv(compose: Path, *, tail: int, follow: bool) -> list[str]:
    """`docker compose logs` for one stack: the last `tail` lines of every service, and with `follow` the new ones too."""
    argv = [*file_argv(compose), "logs", "--tail", str(tail)]
    return [*argv, "--follow"] if follow else argv


def network_command() -> str:
    """Create the shared network unless it exists, as `make up` does."""
    from nexahome.docker import EDGE_NETWORK

    return f"docker network inspect {EDGE_NETWORK} >/dev/null 2>&1 || docker network create {EDGE_NETWORK}"


def up_command(stack: str) -> str:
    return f"docker compose -f stacks/{stack}/compose.yaml up -d --wait"


def down_command(stack: str) -> str:
    return f"docker compose -f stacks/{stack}/compose.yaml down"


def demo_commands(stack: str) -> list[str]:
    """The command lines that start and stop one stack by hand, which `nexahome init` and `nexahome env` print in an
    instance until `nexahome up` exists (PK7)."""
    return [network_command(), up_command(stack), down_command(stack)]


def config_json(runner: Runner, compose: Path) -> RunResult:
    """The stack's resolved configuration as JSON. Variables come from `.env.example`, so the result does not depend
    on a local `.env`. Needs the CLI, not a running engine."""
    env_example = compose.parent / ".env.example"
    argv = file_argv(compose, env_example if env_example.is_file() else None)
    placeholders = _required_placeholders(compose, env_example)
    if placeholders:
        argv = ["env", *placeholders, *argv]
    return runner.run([*argv, "config", "--format", "json"], timeout=COMPOSE_CONFIG_TIMEOUT)


def _required_placeholders(compose: Path, env_example: Path) -> list[str]:
    """`NAME=placeholder` for every `${NAME:?...}` the stack requires and its `.env.example` does not set, so `config`
    can resolve a stack whose script supplies the value (the backup tool). Only the shape of the result is checked."""
    import re

    try:
        text = compose.read_text()
    except OSError:
        return []  # `docker compose config` reports the unreadable file
    if ":?" not in text:  # the common case costs one read and no pattern
        return []
    names = re.findall(r"\$\{([A-Za-z_][A-Za-z0-9_]*):\?", text)
    given = set(re.findall(r"^([A-Za-z_][A-Za-z0-9_]*)=", env_example.read_text(), re.MULTILINE)) if env_example.is_file() else set()
    return [f"{name}=/nexahome-check/{name}" for name in dict.fromkeys(names) if name not in given]
