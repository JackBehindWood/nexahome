"""Every registered command and probe is covered by the same rules, so adding one needs no new rule."""

import pytest

from nexahome import cli
from nexahome.commands import COMMANDS
from nexahome.commands.doctor import PROBES
from nexahome.errors import ExitCode

from conftest import MakeContext, MakeHost


def test_command_names_are_unique() -> None:
    names = [command.NAME for command in COMMANDS]
    assert names and len(names) == len(set(names))


@pytest.mark.parametrize("command", COMMANDS, ids=lambda command: command.NAME)
def test_every_command_has_help(command: object, capsys: pytest.CaptureFixture[str], make_context: MakeContext) -> None:
    assert cli.main([command.NAME, "--help"], make_context()) == ExitCode.OK  # type: ignore[attr-defined]
    assert "usage: nexahome" in capsys.readouterr().out


@pytest.mark.parametrize("command", COMMANDS, ids=lambda command: command.NAME)
def test_every_command_refuses_native_windows(command: object, make_context: MakeContext, make_host: MakeHost) -> None:
    ctx = make_context(host=make_host(system="windows"))
    assert cli.main([command.NAME], ctx) == ExitCode.NOT_READY  # type: ignore[attr-defined]
    assert "Next: wsl --install" in ctx.err.getvalue()  # type: ignore[attr-defined]


def test_top_level_help_lists_every_command(capsys: pytest.CaptureFixture[str], make_context: MakeContext) -> None:
    cli.main(["--help"], make_context())
    out = capsys.readouterr().out
    assert [command.NAME for command in COMMANDS if command.NAME not in out] == []  # type: ignore[attr-defined]


def test_probe_ids_are_unique_and_stable() -> None:
    ids = [probe_id for probe_id, _ in PROBES]
    assert ids == ["platform", "python", "docker-cli", "compose", "engine", "disk", "mount", "env"]
    assert len(ids) == len(set(ids))
