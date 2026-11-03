"""The nexahome command line: loads the command that was asked for, runs it, and owns printing and exit.

Start-up is kept light on purpose ("pay for what you use"): `--version` imports no argparse and no command, and a
command line that names a command imports that command only. tests/test_startup.py enforces it.
"""

from __future__ import annotations

import sys
from collections.abc import Sequence
from typing import TYPE_CHECKING

from nexahome import __version__, commands
from nexahome.errors import ExitCode, NexaHomeError

if TYPE_CHECKING:
    import argparse

    from nexahome.commands._base import Command
    from nexahome.context import Context


def build_parser(selected: "Sequence[Command]") -> "argparse.ArgumentParser":
    import argparse

    parser = argparse.ArgumentParser(prog="nexahome", description="Install, check and run NexaHome.")
    parser.add_argument("--version", action="version", version=f"nexahome {__version__}")
    parser.add_argument("--home", metavar="DIR", help="the NexaHome folder to use (default: $NEXAHOME_HOME, the folder you are in, or ~/nexahome)")
    subparsers = parser.add_subparsers(dest="command", metavar="<command>")
    for command in selected:
        command.register(subparsers)
    return parser


def _command_name(arguments: "Sequence[str]") -> str | None:
    """The first word that is not the leading `--home` option, so `--home DIR config` loads `config` alone."""
    rest = list(arguments)
    if rest and rest[0] == "--home":
        rest = rest[2:]
    elif rest and rest[0].startswith("--home="):
        rest = rest[1:]
    return rest[0] if rest else None


def _reader_went_away() -> int:
    """The reader of our output closed (for example `nexahome doctor | head`): stop quietly, as tools usually do."""
    import os

    os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())  # no second error when the interpreter exits
    return ExitCode.PIPE_CLOSED


def main(argv: Sequence[str] | None = None, ctx: Context | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if arguments == ["--version"]:  # the cheapest and most common call: no argparse, no commands, no context
        try:
            print(f"nexahome {__version__}")
            sys.stdout.flush()
        except BrokenPipeError:
            return _reader_went_away()
        return ExitCode.OK
    # A named command is loaded alone; help, errors and an empty command line need every command's description.
    name = _command_name(arguments)
    selected = [commands.load(name)] if name in commands.names() else commands.load_all()
    parser = build_parser(selected)
    try:
        args = parser.parse_args(arguments)
    except SystemExit as exit_:  # argparse: --help exits 0, usage errors 2
        return int(exit_.code or 0)
    if ctx is None:
        from nexahome.context import Context

        ctx = Context.default()
    if args.home:  # the same setting as $NEXAHOME_HOME, which wins over searching upwards
        ctx.env = {**ctx.env, "NEXAHOME_HOME": args.home}
    if not args.command:
        parser.print_help(ctx.err)
        return ExitCode.USAGE
    try:
        from nexahome.platform import require_supported

        require_supported(ctx.host)
        code = int(args.run(args, ctx))
        ctx.out.flush()  # a closed pipe must surface here, not at interpreter exit
        return code
    except NexaHomeError as error:
        print(f"FAIL  {error.message}\nNext: {error.fix}", file=ctx.err)
        return int(error.exit_code)
    except KeyboardInterrupt:
        return ExitCode.INTERRUPTED
    except BrokenPipeError:
        return _reader_went_away() if ctx.out is sys.stdout else ExitCode.PIPE_CLOSED
    except (OSError, UnicodeDecodeError) as error:  # a file or program the command needed, not a NexaHomeError
        if ctx.env.get("NEXAHOME_DEBUG"):
            raise
        print(f"FAIL  could not read, write or run something: {error}\nNext: nexahome doctor", file=ctx.err)
        return ExitCode.NOT_READY
