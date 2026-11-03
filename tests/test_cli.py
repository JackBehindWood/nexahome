import argparse
import subprocess
import sys
import types
from pathlib import Path
from collections.abc import Callable

import pytest

from nexahome import __version__, cli, commands
from nexahome.commands._base import Subparsers
from nexahome.errors import ExitCode, NexaHomeError

from conftest import MakeContext, MakeHost


def install_command(monkeypatch: pytest.MonkeyPatch, run: Callable[[argparse.Namespace, object], int]) -> None:
    def register(subparsers: Subparsers) -> None:
        subparsers.add_parser("dummy", help="a test command").set_defaults(run=run)

    dummy = types.SimpleNamespace(NAME="dummy", register=register, run=run)
    monkeypatch.setattr(commands, "names", lambda: ("dummy",))
    monkeypatch.setattr(commands, "load", lambda name: dummy)
    monkeypatch.setattr(commands, "load_all", lambda: (dummy,))


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


@pytest.mark.parametrize("error", [PermissionError(13, "Permission denied", "nexahome.toml"), UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid start byte")])
def test_a_file_error_ends_in_one_command_not_a_traceback(
    monkeypatch: pytest.MonkeyPatch, make_context: MakeContext, error: Exception
) -> None:
    def run(args: argparse.Namespace, ctx: object) -> int:
        raise error

    install_command(monkeypatch, run)
    ctx = make_context()
    assert cli.main(["dummy"], ctx) == ExitCode.NOT_READY
    text = ctx.err.getvalue()  # type: ignore[attr-defined]
    assert text.startswith("FAIL  ") and text.endswith("Next: nexahome doctor\n") and "Traceback" not in text


def test_the_debug_setting_keeps_the_traceback(monkeypatch: pytest.MonkeyPatch, make_context: MakeContext) -> None:
    def run(args: argparse.Namespace, ctx: object) -> int:
        raise PermissionError(13, "Permission denied", "nexahome.toml")

    install_command(monkeypatch, run)
    with pytest.raises(PermissionError):
        cli.main(["dummy"], make_context(env={"NEXAHOME_DEBUG": "1"}))


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


def test_a_closed_pipe_ends_quietly_with_141(monkeypatch: pytest.MonkeyPatch, make_context: MakeContext) -> None:
    def run(args: argparse.Namespace, ctx: object) -> int:
        raise BrokenPipeError

    install_command(monkeypatch, run)
    assert cli.main(["dummy"], make_context()) == ExitCode.PIPE_CLOSED == 141


def test_main_reads_sys_argv_and_the_real_context_by_default(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr("sys.argv", ["nexahome", "--version"])
    assert cli.main() == ExitCode.OK
    assert __version__ in capsys.readouterr().out


def test_python_dash_m_works() -> None:
    done = subprocess.run([sys.executable, "-m", "nexahome", "--version"], capture_output=True, text=True, check=False)
    assert (done.returncode, done.stdout.strip()) == (0, f"nexahome {__version__}")


def test_no_arguments_builds_the_real_context_and_shows_help(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr("sys.argv", ["nexahome"])
    assert cli.main() == ExitCode.USAGE
    assert "usage: nexahome" in capsys.readouterr().err


@pytest.mark.skipif(sys.platform == "win32", reason="needs POSIX pipes")
def test_a_reader_that_goes_away_ends_the_process_quietly(tmp_path: Path) -> None:
    import os

    read_end, write_end = os.pipe()
    os.close(read_end)  # nobody reads our output
    done = subprocess.run(
        [sys.executable, "-m", "nexahome", "doctor"], stdout=write_end, stderr=subprocess.PIPE, text=True,
        env={"PATH": str(tmp_path)}, cwd=tmp_path, check=False,
    )
    os.close(write_end)
    assert (done.returncode, done.stderr) == (141, "")


@pytest.mark.skipif(sys.platform == "win32", reason="needs POSIX pipes")
def test_version_to_a_closed_pipe_is_quiet_too(tmp_path: Path) -> None:
    import os

    read_end, write_end = os.pipe()
    os.close(read_end)
    done = subprocess.run([sys.executable, "-m", "nexahome", "--version"], stdout=write_end, stderr=subprocess.PIPE, text=True, cwd=tmp_path, check=False)
    os.close(write_end)
    assert (done.returncode, done.stderr) == (141, "")
