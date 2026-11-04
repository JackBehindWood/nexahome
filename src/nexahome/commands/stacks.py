"""nexahome stacks: list the stacks and whether they run (read-only); `new` and `remove` make and delete your own."""

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
    parser.add_argument("--json", action="store_true", help='print JSON: {"schema": 1, "stacks": [{"name", "enabled", "owner", "state"}]}')
    verbs = parser.add_subparsers(dest="verb", metavar="[new|remove]")
    new = verbs.add_parser("new", help="make a stack of your own from the template", description="Copy the bundled template to stacks/NAME, rename it and enable it in nexahome.toml.")
    new.add_argument("name", metavar="NAME", help="lower-case letters, digits, - and _")
    remove = verbs.add_parser("remove", help="delete a stack you made (never its Docker volumes)", description="Delete stacks/NAME and drop it from nexahome.toml, after listing what goes.")
    remove.add_argument("name", metavar="NAME", help="a stack you made with `nexahome stacks new`")
    remove.add_argument("--yes", action="store_true", help="do not ask before deleting")
    parser.set_defaults(run=run)


def _new(args: argparse.Namespace, ctx: Context) -> int:
    from nexahome.docker import compose
    from nexahome.stacks import scaffold

    instance = ctx.require_instance()
    made = scaffold.new_stack(ctx, instance, args.name)
    shown = ctx.display(made.folder)
    print(f"created {shown}: compose.yaml, .env.example, README.md (default port {made.port}{'; added to nexahome.toml' if made.enabled else ''})", file=ctx.out)
    print(f"Edit the image and settings in {shown}/compose.yaml, then:", file=ctx.out)
    if made.enabled:
        print(f"  nexahome check\n  nexahome env\n  {compose.up_command(args.name)}   (`nexahome up` will replace this)", file=ctx.out)
    else:  # a clone has the Makefile
        print(f"  make check\n  make up STACK={args.name}", file=ctx.out)
    print(f"  curl http://127.0.0.1:{made.port}/", file=ctx.out)
    return ExitCode.OK


def _remove(args: argparse.Namespace, ctx: Context) -> int:
    from nexahome.stacks import scaffold

    scaffold.remove_stack(ctx, ctx.require_instance(), args.name, args.yes)
    return ExitCode.OK


def run(args: argparse.Namespace, ctx: Context) -> int:
    if args.verb == "new":
        return _new(args, ctx)
    if args.verb == "remove":
        return _remove(args, ctx)
    from nexahome.docker import compose
    from nexahome.stacks import catalogue as stack_catalogue
    from nexahome.stacks import ownership
    from nexahome.parallel import map_ordered

    instance = ctx.require_instance()
    owned = ownership.package_owned(instance)
    enabled = set(stack_catalogue.enabled(instance))
    names = stack_catalogue.all_stacks(instance)
    states = map_ordered(lambda name: compose.stack_state(ctx, stack_catalogue.compose_file(instance, name)), names)
    rows = [{"name": name, "enabled": name in enabled, "owner": "package" if name in owned else "user", "state": state} for name, state in zip(names, states, strict=True)]
    if args.json:
        import json

        from nexahome.defaults import STACKS_JSON_SCHEMA

        print(json.dumps({"schema": STACKS_JSON_SCHEMA, "stacks": rows}, indent=2), file=ctx.out)
        return ExitCode.OK
    width = max([len("stack"), *(len(str(row["name"])) for row in rows)])
    print(f"{'stack':<{width}}  enabled  owner    state", file=ctx.out)
    for row in rows:
        print(f"{row['name']:<{width}}  {'yes' if row['enabled'] else 'no':<7}  {row['owner']:<7}  {row['state']}", file=ctx.out)
    return ExitCode.OK
