"""nexahome doctor: read-only diagnosis of this host. Every warning and failure ends in one exact command.

Command modules are thin: they declare the name and the options and import their logic inside run(), so
`nexahome --help` and every other command do not pay for it. The probes are in nexahome/diagnosis.py (to add one,
see the docstring there).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nexahome.errors import ExitCode

if TYPE_CHECKING:
    import argparse

    from nexahome.commands._base import Subparsers
    from nexahome.context import Context

NAME = "doctor"


def register(subparsers: Subparsers) -> None:
    parser = subparsers.add_parser(NAME, help="diagnose this host (read-only)", description=__doc__.split("\n")[0])
    parser.add_argument("--json", action="store_true", help="print the result as JSON (schema 1, see nexahome.report)")
    parser.set_defaults(run=run)


def run(args: argparse.Namespace, ctx: Context) -> int:
    from nexahome import diagnosis
    from nexahome.report import passed, render_json, render_text

    checks = diagnosis.run_probes(ctx)
    print(render_json(checks) if args.json else render_text(checks), file=ctx.out)
    return ExitCode.OK if passed(checks) else ExitCode.NOT_READY
