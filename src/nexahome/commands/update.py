"""nexahome update: update this tool to the newest release. It always checks first and asks before it installs.

`--available` only reports whether a newer version exists. The logic (release source, checksum, installer choice)
is in nexahome/updater.py.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import argparse

    from nexahome.commands._base import Subparsers
    from nexahome.context import Context

NAME = "update"


def register(subparsers: Subparsers) -> None:
    parser = subparsers.add_parser(NAME, help="update nexahome to the newest release", description=__doc__.split("\n")[0])
    parser.add_argument("--available", action="store_true", help="only say whether a newer version exists; install nothing")
    parser.add_argument("--json", action="store_true", help='with --available: {"schema": 1, "installed", "latest", "available"}')
    parser.add_argument("--yes", action="store_true", help="do not ask before installing")
    parser.set_defaults(run=run)


def run(args: argparse.Namespace, ctx: Context) -> int:
    from nexahome.release import updater

    return updater.update(ctx, available_only=args.available, as_json=args.json, assume_yes=args.yes)
