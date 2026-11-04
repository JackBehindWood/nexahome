"""`nexahome.files`: the one place that creates and replaces files (modes, no overwrite, no half-written file)."""

import os
import stat
from pathlib import Path

import pytest

from nexahome import files
from nexahome.errors import NexaHomeError


def mode(path: Path) -> int:
    return stat.S_IMODE(path.stat().st_mode)


@pytest.mark.parametrize("wanted", [0o600, 0o644])
def test_create_exclusive_writes_the_bytes_with_exactly_that_mode_whatever_the_umask(tmp_path: Path, wanted: int) -> None:
    old = os.umask(0o077)  # would strip 0o644 down to 0o600 without the explicit chmod
    try:
        files.create_exclusive(tmp_path / "f", b"data", wanted)
    finally:
        os.umask(old)
    assert (tmp_path / "f").read_bytes() == b"data" and mode(tmp_path / "f") == wanted


def test_create_exclusive_never_overwrites_and_records_only_what_it_made(tmp_path: Path) -> None:
    created: list[Path] = []
    files.create_exclusive(tmp_path / "f", b"first", 0o644, created)
    with pytest.raises(FileExistsError):
        files.create_exclusive(tmp_path / "f", b"second", 0o644, created)
    assert (tmp_path / "f").read_bytes() == b"first" and created == [tmp_path / "f"]


@pytest.mark.parametrize("wanted", [0o600, 0o644])
def test_replace_atomically_swaps_the_text_and_sets_the_mode(tmp_path: Path, wanted: int) -> None:
    (tmp_path / "f").write_text("old")
    files.replace_atomically(tmp_path / "f", "new", wanted)
    assert (tmp_path / "f").read_text() == "new" and mode(tmp_path / "f") == wanted
    assert [p.name for p in tmp_path.iterdir()] == ["f"]  # the temporary file is gone


def test_a_failed_replace_keeps_the_old_file_and_leaves_no_temporary_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / ".env").write_text("old")

    def refuse(source: object, target: object) -> None:
        raise OSError(28, "No space left on device")

    monkeypatch.setattr(os, "replace", refuse)
    with pytest.raises(OSError):
        files.replace_atomically(tmp_path / ".env", "new", 0o600)
    assert (tmp_path / ".env").read_text() == "old" and [p.name for p in tmp_path.iterdir()] == [".env"]


def test_make_directory_creates_missing_parents_and_records_each(tmp_path: Path) -> None:
    created: list[Path] = []
    files.make_directory(tmp_path / "a" / "b", created)
    assert created == [tmp_path / "a", tmp_path / "a" / "b"]
    assert {mode(p) for p in created} == {0o755}
    files.make_directory(tmp_path / "a" / "b", created)  # already there: nothing more to record
    assert len(created) == 2


def test_remove_created_removes_files_and_folders_newest_first_and_ignores_what_is_gone(tmp_path: Path) -> None:
    created: list[Path] = []
    files.make_directory(tmp_path / "a", created)
    files.create_exclusive(tmp_path / "a" / "f", b"x", 0o644, created)
    (tmp_path / "a" / "f").unlink()  # already gone: must not stop the rest
    files.remove_created(created)
    assert not (tmp_path / "a").exists()


# --- Rollback: what a failed create-many-files run does -----------------------------------------------------
def test_rollback_removes_what_the_run_made_and_lets_other_errors_through(tmp_path: Path) -> None:
    created: list[Path] = []
    with pytest.raises(ValueError, match="boom"), files.Rollback(created, "thing", "fix"):
        files.make_directory(tmp_path / "a", created)
        files.create_exclusive(tmp_path / "a" / "f", b"x", 0o644, created)
        raise ValueError("boom")
    assert not (tmp_path / "a").exists()


def test_rollback_turns_an_oserror_into_one_message_and_one_fix(tmp_path: Path) -> None:
    created: list[Path] = []
    with pytest.raises(NexaHomeError) as raised, files.Rollback(created, "init", "nexahome init x"):
        files.create_exclusive(tmp_path / "f", b"x", 0o644, created)
        raise OSError(28, "No space left on device")
    assert raised.value.message == "init stopped and removed what it had made: [Errno 28] No space left on device"
    assert raised.value.fix == "nexahome init x" and isinstance(raised.value.__cause__, OSError)
    assert not (tmp_path / "f").exists()


def test_rollback_keeps_everything_when_the_block_succeeds(tmp_path: Path) -> None:
    created: list[Path] = []
    with files.Rollback(created, "init", "nexahome init x"):
        files.create_exclusive(tmp_path / "f", b"x", 0o644, created)
    assert (tmp_path / "f").exists()


def test_rollback_cleans_up_on_ctrl_c_and_does_not_swallow_it(tmp_path: Path) -> None:
    created: list[Path] = []
    with pytest.raises(KeyboardInterrupt), files.Rollback(created, "init", "nexahome init x"):
        files.create_exclusive(tmp_path / "f", b"x", 0o644, created)
        raise KeyboardInterrupt
    assert not (tmp_path / "f").exists()
