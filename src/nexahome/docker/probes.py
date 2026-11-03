"""The Docker checks of `nexahome doctor`: the CLI, the Compose plugin and the engine (listed in diagnosis.PROBES).

Each answers "what is wrong" with one exact command to fix it; how to install or start Docker differs by system
and comes from nexahome.platform.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nexahome import platform as host_platform
from nexahome.docker import compose, engine
from nexahome.report import Check, Status

if TYPE_CHECKING:
    from collections.abc import Mapping

    from nexahome.context import Context

PROBE_TIMEOUT = 10  # seconds; a stuck VM must not hang the command


def _skip(check_id: str, needs: str) -> Check:
    return Check(check_id, Status.SKIP, f"needs {needs}")


def probe_docker_cli(ctx: Context, prior: Mapping[str, Check]) -> Check:
    """Fail when `docker` is not on the PATH."""
    result = engine.version(ctx, timeout=PROBE_TIMEOUT)
    if not result.ok:
        return Check("docker-cli", Status.FAIL, "Docker CLI not found", host_platform.docker_install_fix(ctx.host))
    return Check("docker-cli", Status.OK, result.stdout.strip().splitlines()[0] if result.stdout.strip() else "found")


def probe_compose(ctx: Context, prior: Mapping[str, Check]) -> Check:
    """Fail when the Compose plugin is missing; skipped without the Docker CLI."""
    if prior["docker-cli"].status != Status.OK:
        return _skip("compose", "docker-cli")
    result = compose.plugin_version(ctx, timeout=PROBE_TIMEOUT)
    if not result.ok:
        return Check("compose", Status.FAIL, "Compose plugin not found", host_platform.compose_install_fix(ctx.host))
    return Check("compose", Status.OK, result.stdout.strip().splitlines()[0] if result.stdout.strip() else "found")


def probe_engine(ctx: Context, prior: Mapping[str, Check]) -> Check:
    """Fail when no container runtime answers `docker info` in time; skipped without the Docker CLI."""
    if prior["docker-cli"].status != Status.OK:
        return _skip("engine", "docker-cli")
    result = engine.info(ctx, timeout=PROBE_TIMEOUT)
    if result.timed_out:
        return Check(
            "engine",
            Status.FAIL,
            f"the container runtime did not answer within {PROBE_TIMEOUT} s",
            host_platform.engine_restart_fix(ctx.host),
        )
    if not result.ok:
        return Check("engine", Status.FAIL, "no container runtime running", host_platform.engine_start_fix(ctx.host))
    return Check("engine", Status.OK, f"running, server {result.stdout.strip() or 'version unknown'}")
