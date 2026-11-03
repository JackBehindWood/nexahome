"""The Docker CLI and the engine behind it: read-only questions."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nexahome.context import Context
    from nexahome.runner import RunResult

TIMEOUT = 15  # seconds


def version(ctx: Context, *, timeout: float = TIMEOUT) -> RunResult:
    """`docker --version`: succeeds when the CLI is installed, with or without a running engine."""
    return ctx.runner.run(["docker", "--version"], timeout=timeout)


def info(ctx: Context, *, timeout: float = TIMEOUT) -> RunResult:
    """`docker info`: succeeds only when an engine answers; stdout is its server version."""
    return ctx.runner.run(["docker", "info", "--format", "{{.ServerVersion}}"], timeout=timeout)
