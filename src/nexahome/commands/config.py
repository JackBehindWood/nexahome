"""nexahome config: show or change the settings in nexahome.toml (which stacks this host runs).

Writes only nexahome.toml, whole and atomically; never touches the stacks, a .env or the manifest.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nexahome.errors import ExitCode

if TYPE_CHECKING:
    import argparse
    from pathlib import Path

    from nexahome.commands._base import Subparsers
    from nexahome.context import Context

NAME = "config"


def register(subparsers: Subparsers) -> None:
    parser = subparsers.add_parser(NAME, help="show or change the settings in nexahome.toml", description=(__doc__ or NAME).split("\n")[0])
    parser.add_argument("action", nargs="?", choices=("list", "get", "set"), default="list", help="list (the default), get KEY, or set KEY VALUE...")
    parser.add_argument("key", nargs="?", metavar="KEY", help="a setting: stacks (settable), schema and created_by (read-only)")
    parser.add_argument("values", nargs="*", metavar="VALUE", help="for set: the new value, for stacks one or more stack names")
    parser.set_defaults(run=run)


def run(args: argparse.Namespace, ctx: Context) -> int:
    from nexahome.errors import NexaHomeError, editor_fix
    from nexahome.instance import CONFIG_NAME, config, home

    root = ctx.require_instance()
    if not home.has_settings(root):
        raise NexaHomeError(
            f"{ctx.display(root)} is a git clone: its stacks are listed in .config/stacks, which the Makefile reads, not in {CONFIG_NAME}",
            editor_fix(".config/stacks"),
        )
    if args.action == "set":
        return _set(args, ctx, root)
    settings = config.read(root)
    if settings is None:  # the file exists, checked above; `assert` would vanish under `python -O`
        raise NexaHomeError("nexahome.toml disappeared while it was being read", "nexahome doctor")
    shown = {"schema": str(settings.schema), "created_by": settings.created_by, "stacks": " ".join(settings.stacks)}
    if args.action == "get":
        if args.key not in shown:
            raise NexaHomeError(f"unknown setting {args.key!r}" if args.key else "get needs a setting", "nexahome config list", ExitCode.USAGE)
        print(shown[args.key], file=ctx.out)
        return ExitCode.OK
    for key in config.KEYS:
        print(f"{key:<12}{shown[key]}{'' if key in config.SETTABLE else '  (read-only)'}", file=ctx.out)
    return ExitCode.OK


def _set(args: argparse.Namespace, ctx: Context, root: Path) -> int:
    from nexahome.errors import NexaHomeError
    from nexahome.instance import config

    if args.key not in config.KEYS:
        raise NexaHomeError(f"unknown setting {args.key!r}" if args.key else "set needs a setting and a value", "nexahome config list", ExitCode.USAGE)
    if args.key not in config.SETTABLE:
        raise NexaHomeError(f"{args.key} is read-only: it describes the file, and only nexahome init writes it", "nexahome config list", ExitCode.USAGE)
    names = config.validate_stacks(root, args.values, "nexahome stacks", ExitCode.USAGE)
    config.write(root, names)
    print(f"{args.key} {' '.join(names)}", file=ctx.out)
    print("Next: nexahome env", file=ctx.out)
    return ExitCode.OK
