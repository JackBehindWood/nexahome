"""nexahome stacks: list the stacks, which this host runs, and whether they are running (read-only)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nexahome.errors import ExitCode

if TYPE_CHECKING:
    import argparse

    from nexahome.commands._base import Subparsers
    from nexahome.context import Context

NAME = "stacks"


def register(subparsers: Subparsers) -> None:
    parser = subparsers.add_parser(NAME, help="list the stacks and their state", description=(__doc__ or NAME).split("\n")[0])
    parser.add_argument("--json", action="store_true", help='print JSON: {"schema": 1, "stacks": [{"name", "enabled", "state"}]}')
    parser.set_defaults(run=run)


def run(args: argparse.Namespace, ctx: Context) -> int:
    from nexahome.docker import compose
    from nexahome.stacks import catalogue as stack_catalogue
    from nexahome.parallel import map_ordered

    instance = ctx.require_instance()
    enabled = set(stack_catalogue.enabled(instance))
    names = stack_catalogue.all_stacks(instance)
    states = map_ordered(lambda name: compose.stack_state(ctx, stack_catalogue.compose_file(instance, name)), names)
    rows = [{"name": name, "enabled": name in enabled, "state": state} for name, state in zip(names, states, strict=True)]
    if args.json:
        import json

        from nexahome.defaults import STACKS_JSON_SCHEMA

        print(json.dumps({"schema": STACKS_JSON_SCHEMA, "stacks": rows}, indent=2), file=ctx.out)
        return ExitCode.OK
    width = max([len("stack"), *(len(str(row["name"])) for row in rows)])
    print(f"{'stack':<{width}}  enabled  state", file=ctx.out)
    for row in rows:
        print(f"{row['name']:<{width}}  {'yes' if row['enabled'] else 'no':<7}  {row['state']}", file=ctx.out)
    return ExitCode.OK
