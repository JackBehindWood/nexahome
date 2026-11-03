"""nexahome init: make a NexaHome folder from the stacks bundled in this install (no clone, no network).

The folder must be new or empty and outside any NexaHome clone or instance; nothing is overwritten and no secret is written.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nexahome.errors import ExitCode

if TYPE_CHECKING:
    import argparse

    from nexahome.commands._base import Subparsers
    from nexahome.context import Context

NAME = "init"


def register(subparsers: Subparsers) -> None:
    parser = subparsers.add_parser(NAME, help="create a NexaHome folder from the bundled stacks", description=(__doc__ or NAME).split("\n")[0])
    parser.add_argument("directory", nargs="?", metavar="DIR", help="the new folder (default: --home, $NEXAHOME_HOME, or ~/nexahome)")
    parser.set_defaults(run=run)


def run(args: argparse.Namespace, ctx: Context) -> int:
    from nexahome import __version__
    from nexahome.docker import compose
    from nexahome.errors import NexaHomeError
    from nexahome.instance import REINSTALL, bundle, create
    from nexahome.defaults import DEMO_PORT, NON_SERVICE_STACKS

    root = create.target(ctx, args.directory)
    create.refuse_unless_new(root)
    source = bundle.location()
    if source is None:
        raise NexaHomeError("this install carries no stacks to copy", REINSTALL)
    made = create.create(root, source, __version__)
    shown = ctx.display(root)
    print(f"created {shown}: {sum(1 for name in made.stacks if name not in NON_SERVICE_STACKS)} stacks, {made.files} files; nexahome.toml enables {', '.join(made.enabled)}", file=ctx.out)
    print(f"Next: cd {shown} && nexahome doctor", file=ctx.out)
    print("\nThen start the demo (needs a running Docker engine; `nexahome up` will replace these lines):", file=ctx.out)
    for line in compose.demo_commands(made.enabled[0]):
        print(f"  {line}", file=ctx.out)
    print(f"  curl http://127.0.0.1:{DEMO_PORT}/", file=ctx.out)
    return ExitCode.OK
