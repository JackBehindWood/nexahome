"""Docker Compose: read-only questions to `docker compose`, and the arguments that name a stack's files."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nexahome.docker import EDGE_NETWORK

if TYPE_CHECKING:
    from pathlib import Path

    from nexahome.context import Context
    from nexahome.runner import Runner, RunResult

TIMEOUT = 15  # seconds
CONFIG_TIMEOUT = 60  # seconds per stack: `config` reads and interpolates every file


def file_argv(compose: Path, env_example: Path | None = None) -> list[str]:
    """`docker compose -f FILE`, plus `--env-file` when the stack's `.env.example` should supply the variables."""
    argv = ["docker", "compose", "-f", str(compose)]
    if env_example is not None:
        argv += ["--env-file", str(env_example)]
    return argv


def plugin_version(ctx: Context, *, timeout: float = TIMEOUT) -> RunResult:
    """`docker compose version`: succeeds when the Compose plugin is installed."""
    return ctx.runner.run(["docker", "compose", "version"], timeout=timeout)


def stack_state(ctx: Context, compose: Path) -> str:
    """"running", "stopped", or "unknown" when Docker cannot answer."""
    result = ctx.runner.run([*file_argv(compose), "ps", "--status", "running", "-q"], timeout=TIMEOUT)
    if not result.ok:
        return "unknown"
    return "running" if result.stdout.strip() else "stopped"


def ps(ctx: Context, compose: Path) -> RunResult:
    return ctx.runner.run([*file_argv(compose), "ps"], timeout=TIMEOUT)


def network_command() -> str:
    """Create the shared network unless it exists, as `make up` does."""
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
    return runner.run([*argv, "config", "--format", "json"], timeout=CONFIG_TIMEOUT)
