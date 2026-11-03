import re
import stat
from collections.abc import Callable
from pathlib import Path

import pytest

from nexahome.stacks import envfile


def counter() -> Callable[[], str]:  # a predictable secret source
    state = {"n": 0}

    def make() -> str:
        state["n"] += 1
        return f"secret{state['n']}"

    return make


def test_placeholders_name_only_the_keys() -> None:
    text = "A=CHANGE_ME\nB=value\n#C=CHANGE_ME\n  D=CHANGE_ME\nE=CHANGE_ME_please\n"
    assert envfile.placeholders(text) == ["A", "E"]


def test_generate_secrets_replaces_only_generate_lines() -> None:
    text = "KEY=GENERATE\nOTHER=keep\nNOT=GENERATE_x\nLAST=GENERATE"
    new, keys = envfile.generate_secrets(text, counter())
    assert new == "KEY=secret1\nOTHER=keep\nNOT=GENERATE_x\nLAST=secret2"
    assert keys == ["KEY", "LAST"]


def test_generate_secrets_also_fills_a_line_that_ends_in_carriage_return() -> None:
    new, keys = envfile.generate_secrets("KEY=GENERATE\r\nOTHER=keep\r\n", counter())  # P-17: CRLF from WSL or a Windows editor
    assert new == "KEY=secret1\r\nOTHER=keep\r\n" and keys == ["KEY"]


def test_real_secrets_are_long_alphanumeric_and_differ() -> None:
    first, second = envfile.new_secret(), envfile.new_secret()
    assert len(first) == 48 and re.fullmatch(r"[A-Za-z0-9]+", first) and first != second


def test_read_value() -> None:
    text = "A=1\nB=\"two words\"\nC='x'\n"
    assert [envfile.read_value(text, k) for k in "ABCD"] == ["1", "two words", "x", None]


def stack(tmp_path: Path, example: str | None = None, env: str | None = None) -> Path:
    directory = tmp_path / "s"
    directory.mkdir()
    if example is not None:
        (directory / ".env.example").write_text(example)
    if env is not None:
        (directory / ".env").write_text(env)
    return directory


def test_prepare_creates_a_private_env_from_the_example(tmp_path: Path) -> None:
    directory = stack(tmp_path, example="PORT=8080\nKEY=GENERATE\n")
    result = envfile.prepare(directory, make=counter())
    assert result is not None and result.created and result.generated == ("KEY",) and result.pending == ()
    assert (directory / ".env").read_text() == "PORT=8080\nKEY=secret1\n"
    assert stat.S_IMODE((directory / ".env").stat().st_mode) == 0o600
    assert (directory / ".env.example").read_text() == "PORT=8080\nKEY=GENERATE\n"  # the example is never touched


def test_prepare_waits_for_placeholders_before_generating(tmp_path: Path) -> None:
    directory = stack(tmp_path, example="NAME=CHANGE_ME\nKEY=GENERATE\n")
    result = envfile.prepare(directory, make=counter())
    assert result is not None and result.pending == ("NAME",) and result.generated == ()
    assert (directory / ".env").read_text() == "NAME=CHANGE_ME\nKEY=GENERATE\n"
    (directory / ".env").write_text("NAME=mine\nKEY=GENERATE\n")  # the user fills it in
    again = envfile.prepare(directory, make=counter())
    assert again is not None and not again.created and again.generated == ("KEY",)
    assert (directory / ".env").read_text() == "NAME=mine\nKEY=secret1\n"
    assert stat.S_IMODE((directory / ".env").stat().st_mode) == 0o600


def test_prepare_never_overwrites_and_is_idempotent(tmp_path: Path) -> None:
    directory = stack(tmp_path, example="KEY=GENERATE\n", env="KEY=mine\n")
    result = envfile.prepare(directory)
    assert result is not None and not result.created and result.generated == () and result.pending == ()
    assert (directory / ".env").read_text() == "KEY=mine\n"


def test_dry_run_writes_nothing(tmp_path: Path) -> None:
    directory = stack(tmp_path, example="KEY=GENERATE\n")
    result = envfile.prepare(directory, dry_run=True)
    assert result is not None and result.created and result.generated == ("KEY",)
    assert not (directory / ".env").exists()


def test_dry_run_leaves_an_existing_env_alone(tmp_path: Path) -> None:
    directory = stack(tmp_path, env="KEY=GENERATE\n")
    result = envfile.prepare(directory, dry_run=True)
    assert result is not None and result.generated == ("KEY",)
    assert (directory / ".env").read_text() == "KEY=GENERATE\n"


def test_a_stack_without_env_files_is_skipped(tmp_path: Path) -> None:
    assert envfile.prepare(stack(tmp_path)) is None


def test_a_failed_rewrite_leaves_the_env_untouched_and_no_temporary_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    directory = stack(tmp_path, env="KEY=GENERATE\n")

    def broken(source: object, target: object) -> None:
        raise OSError("disk full")

    monkeypatch.setattr(envfile.os, "replace", broken)
    with pytest.raises(OSError, match="disk full"):
        envfile.prepare(directory, make=counter())
    assert (directory / ".env").read_text() == "KEY=GENERATE\n"
    assert sorted(p.name for p in directory.iterdir()) == [".env"]
