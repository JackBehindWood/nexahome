"""nexahome env: prepare this checkout for `make up`: create each stack's .env, generate its secrets, run doctor.

Writes only inside the NexaHome folder (an instance or a clone), never overwrites a .env, never prints a secret, and starts nothing.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nexahome.errors import ExitCode

if TYPE_CHECKING:
    import argparse
    from pathlib import Path

    from nexahome.commands._base import Subparsers
    from nexahome.context import Context

NAME = "env"


def register(subparsers: Subparsers) -> None:
    parser = subparsers.add_parser(NAME, help="create each stack's .env, generate secrets, then run doctor", description=__doc__.split("\n")[0])
    parser.add_argument("--stack", metavar="NAME", help="only this stack (default: the stacks this host runs)")
    parser.add_argument("--dry-run", action="store_true", help="show what would change and write nothing")
    parser.set_defaults(run=run)


def _require_ignored(ctx: Context, checkout: Path, env_path: Path) -> None:
    """Secrets must never land in a path git would commit. Skipped when git cannot answer."""
    from nexahome.errors import NexaHomeError

    relative = env_path.relative_to(checkout)
    result = ctx.runner.run(["git", "-C", str(checkout), "check-ignore", "-q", str(relative)], timeout=10)
    if result.returncode == 1 and not result.missing and not result.timed_out:
        raise NexaHomeError(f"{relative} is not gitignored; refusing to write secrets there", f"git check-ignore -v {relative}")


def run(args: argparse.Namespace, ctx: Context) -> int:
    from nexahome import diagnosis, envfile
    from nexahome import stacks as stack_catalogue
    from nexahome.errors import NexaHomeError
    from nexahome.report import passed, render_text

    checkout = ctx.require_checkout()
    if args.stack and not stack_catalogue.compose_file(checkout, args.stack).is_file():
        raise NexaHomeError(f"no such stack: {args.stack}", "nexahome stacks")
    names = [args.stack] if args.stack else stack_catalogue.enabled(checkout)
    pending = False
    for name in names:
        stack_dir = checkout / "stacks" / name
        _require_ignored(ctx, checkout, stack_dir / ".env")
        result = envfile.prepare(stack_dir, dry_run=args.dry_run)
        if result is None:
            continue
        shown = ctx.display(result.path)
        if result.created:
            print(f"{'would create' if args.dry_run else 'created'} {shown} from .env.example", file=ctx.out)
        if result.generated:
            if args.dry_run:
                print(f"would generate {len(result.generated)} secret(s) in {shown}", file=ctx.out)
            else:
                print(f"generated secrets in {shown} (not shown); copy them to your password manager", file=ctx.out)
        if result.pending:
            pending = True
            print(f"{shown}: set a real value for each of these, then run nexahome env again:", file=ctx.out)
            for key in result.pending:
                print(f"  {key}", file=ctx.out)
        elif not (result.created or result.generated):
            print(f"ok    {shown} is ready", file=ctx.out)
    print(file=ctx.out)
    checks = diagnosis.run_probes(ctx)
    print(render_text(checks), file=ctx.out)
    if passed(checks) and not pending:
        if (checkout / "Makefile").is_file():
            print("Next: make up", file=ctx.out)
        else:  # an instance made by `nexahome init` has no Makefile; `nexahome up` does not exist yet (PK7)
            from nexahome.docker import compose

            print(f"Next: {compose.network_command()}", file=ctx.out)
            print("Then start each stack (`nexahome up` will replace these lines):", file=ctx.out)
            for name in names:
                print(f"  {compose.up_command(name)}", file=ctx.out)
        return ExitCode.OK
    return ExitCode.NOT_READY
