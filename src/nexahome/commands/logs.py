"""nexahome logs: show the logs of the stacks this host runs (read-only, `docker compose logs` on the host)."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import argparse

    from nexahome.commands._base import Subparsers
    from nexahome.context import Context

NAME = "logs"


def register(subparsers: Subparsers) -> None:
    parser = subparsers.add_parser(NAME, help="show the logs of a stack", description=(__doc__ or NAME).split("\n")[0])
    parser.add_argument("stack", nargs="?", metavar="STACK", help="a stack this host runs (default: every one, in turn)")
    parser.add_argument("--tail", type=int, default=None, metavar="N", help="lines per service from the end (default 100)")
    parser.add_argument("--follow", action="store_true", help="keep printing new lines until Ctrl-C (needs STACK)")
    parser.set_defaults(run=run)


def run(args: argparse.Namespace, ctx: Context) -> int:
    from nexahome.defaults import LOG_TAIL
    from nexahome.stacks import logs

    return logs.show(ctx, ctx.require_instance(), args.stack, LOG_TAIL if args.tail is None else args.tail, args.follow)
