"""The nexahome command line: builds the parser from COMMANDS, runs one command, owns printing and exit."""

import argparse
import os
import sys
from collections.abc import Sequence

from nexahome import __version__
from nexahome.commands import COMMANDS
from nexahome.context import Context
from nexahome.errors import ExitCode, NexaHomeError
from nexahome.platform import require_supported


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="nexahome", description="Install, check and run NexaHome.")
    parser.add_argument("--version", action="version", version=f"nexahome {__version__}")
    subparsers = parser.add_subparsers(dest="command", metavar="<command>")
    for command in COMMANDS:
        command.register(subparsers)
    return parser


def main(argv: Sequence[str] | None = None, ctx: Context | None = None) -> int:
    ctx = ctx or Context.default()
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exit_:  # argparse: --help and --version exit 0, usage errors 2
        return int(exit_.code or 0)
    if not args.command:
        parser.print_help(ctx.err)
        return ExitCode.USAGE
    try:
        require_supported(ctx.host)
        return int(args.run(args, ctx))
    except NexaHomeError as error:
        print(f"FAIL  {error.message}\nNext: {error.fix}", file=ctx.err)
        return int(error.exit_code)
    except KeyboardInterrupt:
        return ExitCode.INTERRUPTED
    except BrokenPipeError:  # the reader went away, for example `nexahome doctor | head`
        if ctx.out is sys.stdout:
            os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())  # no second error at exit
        return ExitCode.PIPE_CLOSED
