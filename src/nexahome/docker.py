"""Read-only questions to the Docker CLI that more than one command asks."""

from pathlib import Path

from nexahome.context import Context
from nexahome.runner import RunResult

TIMEOUT = 15  # seconds


def engine_info(ctx: Context) -> RunResult:
    return ctx.runner.run(["docker", "info", "--format", "{{.ServerVersion}}"], timeout=TIMEOUT)


def stack_state(ctx: Context, compose: Path) -> str:
    """"running", "stopped", or "unknown" when Docker cannot answer."""
    result = ctx.runner.run(["docker", "compose", "-f", str(compose), "ps", "--status", "running", "-q"], timeout=TIMEOUT)
    if not result.ok:
        return "unknown"
    return "running" if result.stdout.strip() else "stopped"


def compose_ps(ctx: Context, compose: Path) -> RunResult:
    return ctx.runner.run(["docker", "compose", "-f", str(compose), "ps"], timeout=TIMEOUT)
