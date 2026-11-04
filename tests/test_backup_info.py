import os
from pathlib import Path

from nexahome import backup_info

DAY = 24 * 3600
NOW = 1_000_000_000.0


def repository(tmp_path: Path, ages_in_days: list[float]) -> Path:
    directory = tmp_path / "repo"
    (directory / "snapshots").mkdir(parents=True)
    (directory / "config").write_text("x" * 100)
    for number, age in enumerate(ages_in_days):
        snapshot = directory / "snapshots" / f"s{number}"
        snapshot.write_text("y" * 10)
        os.utime(snapshot, (NOW - age * DAY, NOW - age * DAY))
    return directory


def test_no_repository(tmp_path: Path) -> None:
    assert backup_info.summary(tmp_path / "none", NOW, clone=True) == [f"backup: no repository at {tmp_path / 'none'} (in a git clone: make backup-init)"]


def test_empty_recent_and_old_repositories(tmp_path: Path) -> None:
    assert backup_info.summary(repository(tmp_path, []), NOW, clone=True)[0] == "backup: repository has no snapshots yet (in a git clone: make backup)"
    recent = tmp_path / "a"
    recent.mkdir()
    assert backup_info.summary(repository(recent, [30, 2]), NOW, clone=True)[0] == "backup: last snapshot within 7 days"
    old = tmp_path / "b"
    old.mkdir()
    assert backup_info.summary(repository(old, [30, 8]), NOW, clone=True)[0] == "backup: last snapshot OLDER than 7 days (in a git clone: make backup)"


def test_an_instance_is_never_told_to_run_make(tmp_path: Path) -> None:
    """A-02: an instance made by `nexahome init` has no Makefile, so the hint says what is true instead."""
    hint = "not available in an instance yet"
    assert backup_info.summary(tmp_path / "none", NOW, clone=False) == [f"backup: no repository at {tmp_path / 'none'} ({hint})"]
    assert backup_info.summary(repository(tmp_path, []), NOW, clone=False)[0] == f"backup: repository has no snapshots yet ({hint})"
    old = tmp_path / "b"
    old.mkdir()
    assert backup_info.summary(repository(old, [30, 8]), NOW, clone=False)[0] == f"backup: last snapshot OLDER than 7 days ({hint})"


def test_a_file_that_vanishes_or_dangles_is_skipped_not_a_crash(tmp_path: Path) -> None:
    directory = repository(tmp_path, [1])
    (directory / "snapshots" / "gone").symlink_to(directory / "nowhere")  # P-04: restic prunes while status walks
    assert backup_info.summary(directory, NOW, clone=True)[0] == "backup: last snapshot within 7 days"


def test_the_size_line(tmp_path: Path) -> None:
    directory = repository(tmp_path, [1])
    assert backup_info.summary(directory, NOW, clone=True)[1] == f"backup: repository size 110B in {directory}"


def test_human_size() -> None:
    assert [backup_info.human_size(n) for n in (0, 1023, 1024, 1536, 5 * 1024**2, 3 * 1024**3)] == ["0B", "1023B", "1.0K", "1.5K", "5.0M", "3.0G"]
    assert backup_info.human_size(5 * 1024**5) == "5120.0T"  # the largest unit stops the scaling


def test_repository_dir_precedence(tmp_path: Path) -> None:
    (tmp_path / "stacks" / "backup").mkdir(parents=True)
    assert backup_info.repository_dir(tmp_path, {}) == tmp_path / "data" / "backup"
    assert backup_info.repository_dir(tmp_path, {"NEXAHOME_BACKUP_DIR": "/from/env"}) == Path("/from/env")
    (tmp_path / "stacks" / "backup" / ".env").write_text('NEXAHOME_BACKUP_DIR="/from/file"\n')
    assert backup_info.repository_dir(tmp_path, {"NEXAHOME_BACKUP_DIR": "/from/env"}) == Path("/from/file")
