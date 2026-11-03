"""nexahome check: the Compose policy over the stacks (read-only; needs the Docker CLI, not a running engine)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nexahome.errors import ExitCode

if TYPE_CHECKING:
    import argparse

    from nexahome.commands._base import Subparsers
    from nexahome.context import Context

NAME = "check"


def register(subparsers: Subparsers) -> None:
    parser = subparsers.add_parser(NAME, help="check the stacks against the Compose policy", description=(__doc__ or NAME).split("\n")[0])
    parser.add_argument("--stacks", metavar="DIR", help="the folder that holds the stacks (default: stacks/ of the instance or clone)")
    parser.set_defaults(run=run)


def run(args: argparse.Namespace, ctx: Context) -> int:
    from nexahome import platform as host_platform
    from nexahome.errors import NexaHomeError
    from nexahome.policy import compose

    root = ctx.cwd / args.stacks if args.stacks else (ctx.instance() or ctx.cwd) / "stacks"
    try:  # messages read stacks/x/... when the folder is inside the working directory
        shown = root.relative_to(ctx.cwd)
    except ValueError:
        shown = root
    results = compose.check_stacks(ctx.runner, root, shown)
    if not results:
        raise NexaHomeError(f"no stacks found in {ctx.display(root)}; nothing to check", f"ls {ctx.display(root)}" if args.stacks else "nexahome init")
    if any(result.docker_missing for result in results):
        raise NexaHomeError("docker CLI not found; cannot validate stacks", host_platform.docker_install_fix(ctx.host))
    failures = 0
    for result in results:
        for line in result.lines():
            print(line, file=ctx.out)
        if result.error:
            print(result.error, file=ctx.err)
        failures += len(result.problems) + (result.error is not None)
    return ExitCode.FAILED if failures else ExitCode.OK
