import argparse
import types
from collections.abc import Callable

import pytest

from nexahome import __version__, cli
from nexahome.errors import ExitCode, NexaHomeError

from conftest import MakeContext, MakeHost


def install_command(monkeypatch: pytest.MonkeyPatch, run: Callable[[argparse.Namespace, object], int]) -> None:
    def register(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
        subparsers.add_parser("dummy", help="a test command").set_defaults(run=run)

    dummy = types.SimpleNamespace(NAME="dummy", register=register, run=run)
    monkeypatch.setattr(cli, "COMMANDS", (dummy,))


def test_version(capsys: pytest.CaptureFixture[str], make_context: MakeContext) -> None:
    assert cli.main(["--version"], make_context()) == ExitCode.OK
    assert capsys.readouterr().out.strip() == f"nexahome {__version__}"


def test_no_command_prints_help_and_exits_2(make_context: MakeContext) -> None:
    ctx = make_context()
    assert cli.main([], ctx) == ExitCode.USAGE
    assert "usage: nexahome" in ctx.err.getvalue()  # type: ignore[attr-defined]


def test_unknown_command_is_a_usage_error(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch, make_context: MakeContext
) -> None:
    install_command(monkeypatch, lambda args, ctx: 0)
    assert cli.main(["nope"], make_context()) == ExitCode.USAGE
    assert "invalid choice" in capsys.readouterr().err


def test_command_return_value_is_the_exit_code(monkeypatch: pytest.MonkeyPatch, make_context: MakeContext) -> None:
    install_command(monkeypatch, lambda args, ctx: 1)
    assert cli.main(["dummy"], make_context()) == 1


def test_error_prints_fail_and_next_and_uses_its_exit_code(
    monkeypatch: pytest.MonkeyPatch, make_context: MakeContext
) -> None:
    def run(args: argparse.Namespace, ctx: object) -> int:
        raise NexaHomeError("engine is down", "colima start", ExitCode.FAILED)

    install_command(monkeypatch, run)
    ctx = make_context()
    assert cli.main(["dummy"], ctx) == ExitCode.FAILED
    assert ctx.err.getvalue() == "FAIL  engine is down\nNext: colima start\n"  # type: ignore[attr-defined]


def test_error_without_a_fix_is_refused() -> None:
    with pytest.raises(ValueError):
        NexaHomeError("broken", " ")


def test_interrupt_exits_130(monkeypatch: pytest.MonkeyPatch, make_context: MakeContext) -> None:
    def run(args: argparse.Namespace, ctx: object) -> int:
        raise KeyboardInterrupt

    install_command(monkeypatch, run)
    assert cli.main(["dummy"], make_context()) == ExitCode.INTERRUPTED


def test_native_windows_is_refused_before_the_command_runs(
    monkeypatch: pytest.MonkeyPatch, make_context: MakeContext, make_host: MakeHost
) -> None:
    ran: list[bool] = []
    install_command(monkeypatch, lambda args, ctx: ran.append(True) or 0)
    ctx = make_context(host=make_host(system="windows"))
    assert cli.main(["dummy"], ctx) == ExitCode.NOT_READY
    err = ctx.err.getvalue()  # type: ignore[attr-defined]
    assert "WSL2" in err and err.endswith("Next: wsl --install\n")
    assert not ran
