"""The logs of the stacks this host runs, read with `docker compose logs` on the host: no Docker socket handed to a
container, no new dependency (ADR 0013 keeps the portal and the health tool away from logs)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nexahome.errors import ExitCode, NexaHomeError

if TYPE_CHECKING:
    from pathlib import Path

    from nexahome.context import Context


def show(ctx: Context, instance: Path, stack: str | None, tail: int, follow: bool) -> int:
    """Print the last `tail` lines of `stack`, or of every enabled stack in turn. `follow` needs one stack."""
    from nexahome import platform as host_platform
    from nexahome.defaults import LOGS_TIMEOUT, NON_SERVICE_STACKS
    from nexahome.docker import compose, engine
    from nexahome.stacks import catalogue

    if tail < 1:
        raise NexaHomeError(f"--tail needs a number of lines, 1 or more (not {tail})", "nexahome logs --tail 100", ExitCode.USAGE)
    names = [name for name in catalogue.enabled(instance) if name not in NON_SERVICE_STACKS]
    if stack is not None and stack not in names:
        raise NexaHomeError(f"{stack} is not a stack this host runs", "nexahome stacks")
    if not names:
        raise NexaHomeError("no stacks to show", "nexahome stacks")
    if follow and stack is None:
        raise NexaHomeError("--follow follows one stack at a time", f"nexahome logs {names[0]} --follow", ExitCode.USAGE)
    if not engine.info(ctx).ok:
        raise NexaHomeError("no container runtime running", host_platform.engine_start_fix(ctx.host))
    chosen = [stack] if stack is not None else names
    for position, name in enumerate(chosen):
        argv = compose.logs_argv(catalogue.compose_file(instance, name), tail=tail, follow=follow)
        if follow:
            ctx.out.flush()
            if ctx.runner.stream(argv) != 0:
                raise NexaHomeError(f"could not follow the logs of {name}", "nexahome doctor")
            continue
        result = ctx.runner.run(argv, timeout=LOGS_TIMEOUT)
        if not result.ok:
            reason = (result.stderr.strip().splitlines() or ["docker compose logs failed"])[-1]
            raise NexaHomeError(f"could not read the logs of {name}: {reason}", "nexahome doctor")
        if stack is None:
            print(f"{'' if position == 0 else chr(10)}==> {name} <==", file=ctx.out)
        if result.stdout:
            print(result.stdout.rstrip("\n"), file=ctx.out)
        else:
            print(f"{name}: no log lines; is it running? Check with: nexahome stacks", file=ctx.err)
    return ExitCode.OK
