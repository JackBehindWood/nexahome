"""nexahome status: how the stacks and the backup are doing (read-only)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nexahome.errors import ExitCode

if TYPE_CHECKING:
    import argparse

    from nexahome.commands._base import Subparsers
    from nexahome.context import Context

NAME = "status"


def register(subparsers: Subparsers) -> None:
    parser = subparsers.add_parser(NAME, help="show stack health and how recent the backup is", description=(__doc__ or NAME).split("\n")[0])
    parser.set_defaults(run=run)


def run(args: argparse.Namespace, ctx: Context) -> int:
    from nexahome import backup_info
    from nexahome.docker import compose, engine
    from nexahome import platform as host_platform
    from nexahome.stacks import catalogue as stack_catalogue
    from nexahome.parallel import map_ordered

    instance = ctx.require_instance()
    if engine.info(ctx).ok:
        names = stack_catalogue.enabled(instance)
        results = map_ordered(lambda name: compose.ps(ctx, stack_catalogue.compose_file(instance, name)), names)
        for name, result in zip(names, results, strict=True):
            print(result.stdout.rstrip() if result.ok else f"{name}: could not read its state (docker compose ps failed); run: nexahome doctor", file=ctx.out)
    else:
        print(f"no container runtime running; start it with: {host_platform.engine_start_fix(ctx.host)}", file=ctx.out)
    directory = backup_info.repository_dir(instance, ctx.env)
    print("\n".join(backup_info.summary(directory, ctx.now())), file=ctx.out)
    return ExitCode.OK
