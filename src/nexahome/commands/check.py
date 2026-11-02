"""nexahome check: the Compose policy over the stacks (read-only; needs the Docker CLI, not a running engine)."""

import argparse

from nexahome import platform as host_platform
from nexahome.commands._base import Subparsers
from nexahome.context import Context
from nexahome.errors import ExitCode, NexaHomeError
from nexahome.policy import compose

NAME = "check"


def register(subparsers: Subparsers) -> None:
    parser = subparsers.add_parser(NAME, help="check the stacks against the Compose policy", description=__doc__.split("\n")[0])
    parser.add_argument("--stacks", metavar="DIR", help="the folder that holds the stacks (default: stacks/ of the checkout)")
    parser.set_defaults(run=run)


def run(args: argparse.Namespace, ctx: Context) -> int:
    root = ctx.cwd / args.stacks if args.stacks else (ctx.checkout() or ctx.cwd) / "stacks"
    try:  # messages read stacks/x/... when the folder is inside the working directory
        shown = root.relative_to(ctx.cwd)
    except ValueError:
        shown = root
    results = compose.check_stacks(ctx.runner, root, shown)
    if not results:
        print("no stacks found; nothing to check", file=ctx.out)
        return ExitCode.NOT_READY
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
