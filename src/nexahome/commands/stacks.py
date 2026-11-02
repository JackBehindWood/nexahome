"""nexahome stacks: list the stacks, which this host runs, and whether they are running (read-only)."""

import argparse
import json

from nexahome import docker
from nexahome import stacks as stack_catalogue
from nexahome.commands._base import Subparsers
from nexahome.context import Context
from nexahome.errors import ExitCode

NAME = "stacks"


def register(subparsers: Subparsers) -> None:
    parser = subparsers.add_parser(NAME, help="list the stacks and their state", description=__doc__.split("\n")[0])
    parser.add_argument("--json", action="store_true", help='print JSON: {"schema": 1, "stacks": [{"name", "enabled", "state"}]}')
    parser.set_defaults(run=run)


def run(args: argparse.Namespace, ctx: Context) -> int:
    checkout = ctx.require_checkout()
    enabled = set(stack_catalogue.enabled(checkout))
    rows = [
        {"name": name, "enabled": name in enabled, "state": docker.stack_state(ctx, stack_catalogue.compose_file(checkout, name))}
        for name in stack_catalogue.all_stacks(checkout)
    ]
    if args.json:
        print(json.dumps({"schema": 1, "stacks": rows}, indent=2), file=ctx.out)
        return ExitCode.OK
    width = max([len("stack"), *(len(str(row["name"])) for row in rows)])
    print(f"{'stack':<{width}}  enabled  state", file=ctx.out)
    for row in rows:
        print(f"{row['name']:<{width}}  {'yes' if row['enabled'] else 'no':<7}  {row['state']}", file=ctx.out)
    return ExitCode.OK
