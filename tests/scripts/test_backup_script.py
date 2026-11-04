"""Golden tests for scripts/backup.sh: what it refuses, says and runs, with a stub `docker` (no engine, no restic).

Characterisation: they pin today's behaviour so the port to the package (PK8) has an oracle (ADR 0018, PK-C3).
To reproduce a failure by hand, run `sh scripts/backup.sh <arguments>` in a checkout.
"""

import os
import subprocess
import time
from pathlib import Path

import pytest

from nexahome import backup_info
from script_harness import Rule, calls, install_stub, make_tree, run_script

DAY = 24 * 3600
USAGE = "backup: usage: scripts/backup.sh init | backup [stack] | restore <stack> | verify [stack] | check | snapshots | fingerprint <volume> | status | restic <arguments>"
RUNNING: Rule = ("info", 0, "")
LABELLED: list[Rule] = [
    RUNNING,
    ("volume ls -q --filter label=nexahome.backup=true", 0, "nexahome-actual_data"),
    ("volume inspect -f *", 0, "nexahome-actual"),
    ("compose -f stacks/backup/compose.yaml run --rm -T -v * --entrypoint stat *", 0, "1000"),
]


@pytest.fixture
def tree(tmp_path: Path) -> Path:
    root = make_tree(tmp_path, ("backup.sh",))
    (root / "stacks" / "backup").mkdir(parents=True)
    (root / "stacks" / "backup" / "compose.yaml").write_text("services: {}\n")
    (root / "stacks" / "actual").mkdir()
    (root / "stacks" / "actual" / "compose.yaml").write_text("services: {}\n")
    return root


def with_repository(root: Path, mode: int = 0o600) -> Path:
    """A password file and a repository folder, as `make backup-init` leaves them."""
    password = root / ".config" / "restic-password"
    password.parent.mkdir(exist_ok=True)
    password.write_text("not-a-real-password")
    password.chmod(mode)
    repository = root / "data" / "backup"
    (repository / "snapshots").mkdir(parents=True, exist_ok=True)
    (repository / "config").write_text("")
    return repository


def sh(root: Path, tmp_path: Path, rules: list[Rule], *args: str, env: dict[str, str] | None = None) -> tuple[subprocess.CompletedProcess[str], Path]:
    bin_dir = tmp_path / "bin"
    log = install_stub(bin_dir, "docker", rules)
    return run_script(root, "backup.sh", *args, bin_dir=bin_dir, env=env), log


def test_without_a_known_command_it_prints_the_usage(tree: Path, tmp_path: Path) -> None:
    for args in ((), ("nonsense",)):
        done, _ = sh(tree, tmp_path, [], *args)
        assert (done.returncode, done.stderr.strip()) == (1, USAGE)


def test_no_container_runtime_names_colima(tree: Path, tmp_path: Path) -> None:
    done, _ = sh(tree, tmp_path, [("info", 1, "")], "snapshots")
    assert done.returncode == 1
    assert "no container runtime is running" in done.stderr and "colima start --cpu 2 --memory 2 --disk 20" in done.stderr


def test_a_missing_password_file_says_how_to_create_it(tree: Path, tmp_path: Path) -> None:
    done, _ = sh(tree, tmp_path, [RUNNING], "snapshots")
    assert done.returncode == 1
    assert f"password file missing: {tree}/.config/restic-password. Run 'make backup-init'" in done.stderr


def test_a_password_file_others_can_read_is_refused_with_the_chmod(tree: Path, tmp_path: Path) -> None:
    with_repository(tree, mode=0o640)
    done, _ = sh(tree, tmp_path, [RUNNING], "snapshots")
    assert done.returncode == 1
    assert f"password file is readable by others; run: chmod 600 '{tree}/.config/restic-password'" in done.stderr


def test_a_missing_repository_names_the_folder_and_the_fix(tree: Path, tmp_path: Path) -> None:
    (tree / ".config").mkdir()
    password = tree / ".config" / "restic-password"
    password.write_text("x")
    password.chmod(0o600)
    done, _ = sh(tree, tmp_path, [RUNNING], "check")
    assert done.returncode == 1
    assert f"no repository at {tree}/data/backup. Run 'make backup-init'" in done.stderr


def test_backup_with_no_labelled_volume_says_to_start_a_stack(tree: Path, tmp_path: Path) -> None:
    with_repository(tree)
    done, _ = sh(tree, tmp_path, [RUNNING, ("volume ls *", 0, "")], "backup")
    assert (done.returncode, done.stderr.strip()) == (1, "backup: no volume is labelled nexahome.backup=true; start a stack first (make up).")


def test_backup_of_an_unlabelled_stack_is_refused(tree: Path, tmp_path: Path) -> None:
    with_repository(tree)
    done, _ = sh(tree, tmp_path, LABELLED, "backup", "hello")
    assert (done.returncode, done.stderr.strip()) == (1, "backup: no labelled volume for stack 'hello'.")


def test_restore_needs_a_stack_that_exists(tree: Path, tmp_path: Path) -> None:
    done, _ = sh(tree, tmp_path, [], "restore")
    assert (done.returncode, done.stderr.strip()) == (1, "backup: usage: make restore STACK=name [SNAPSHOT=id] [TARGET=suffix]  (ids: make snapshots)")
    done, _ = sh(tree, tmp_path, [], "restore", "ghost")
    assert (done.returncode, done.stderr.strip()) == (1, "backup: no such stack: ghost")


def test_restore_without_a_snapshot_points_at_the_list(tree: Path, tmp_path: Path) -> None:
    with_repository(tree)
    done, _ = sh(tree, tmp_path, [RUNNING, ("compose -f stacks/backup/compose.yaml run --rm -T restic ls *", 0, "")], "restore", "actual")
    assert (done.returncode, done.stderr.strip()) == (1, "backup: no snapshot of stack 'actual' found (snapshot: latest). See: make snapshots")


def test_restore_never_overwrites_an_existing_volume(tree: Path, tmp_path: Path) -> None:
    with_repository(tree)
    rules: list[Rule] = [
        RUNNING,
        ("compose -f stacks/backup/compose.yaml run --rm -T restic ls *", 0, "/data/nexahome-actual_data"),
        ("volume inspect nexahome-actual_data", 0, ""),
    ]
    done, log = sh(tree, tmp_path, rules, "restore", "actual", env={"TARGET": ""})
    assert done.returncode == 1
    assert "volume nexahome-actual_data already exists; restore does not overwrite. For a separate copy add TARGET=<suffix>." in done.stderr
    assert not [c for c in calls(log) if "restore" in c.split("|", 1)[1].split()[-3:] or " create" in c]


def test_restore_into_a_target_names_the_new_project_and_how_to_remove_it(tree: Path, tmp_path: Path) -> None:
    with_repository(tree)
    rules: list[Rule] = [
        ("volume inspect *", 1, ""),
        ("compose -f stacks/backup/compose.yaml run --rm -T restic ls *", 0, "/data/nexahome-actual_data"),
        ("compose -f stacks/backup/compose.yaml run --rm -T -v * --entrypoint stat *", 0, "1000"),
        ("compose -p nexahome-actual-copy create", 0, ""),
        ("compose -f stacks/backup/compose.yaml run --rm -T --user 1000:1000 -v nexahome-actual-copy_data:/data/nexahome-actual_data restic restore latest --tag stack=actual --target / --include /data/nexahome-actual_data --verify", 0, ""),
        RUNNING,
    ]
    done, log = sh(tree, tmp_path, rules, "restore", "actual", env={"TARGET": "copy"})
    assert done.returncode == 0, done.stderr
    assert "restoring nexahome-actual_data into volume nexahome-actual-copy_data" in done.stdout
    assert "Restored into project nexahome-actual-copy (snapshot: latest)" in done.stdout
    assert "Remove it:  (cd stacks/actual && docker compose -p nexahome-actual-copy down -v)" in done.stdout
    assert any("restic restore latest" in c for c in calls(log))


def test_init_refuses_to_overwrite_a_password_file_or_a_repository(tree: Path, tmp_path: Path) -> None:
    repository = with_repository(tree)
    done, _ = sh(tree, tmp_path, [RUNNING], "init")
    assert (done.returncode, done.stderr.strip()) == (1, f"backup: password file already exists: {tree}/.config/restic-password (not overwriting)")
    (tree / ".config" / "restic-password").unlink()
    done, _ = sh(tree, tmp_path, [RUNNING], "init")
    assert (done.returncode, done.stderr.strip()) == (1, f"backup: a repository already exists at {repository} (not overwriting)")


def test_init_will_not_write_inside_a_repository_that_does_not_ignore_the_path(tree: Path, tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=tree, check=True)  # no .gitignore: .config/ and data/ are not ignored
    done, log = sh(tree, tmp_path, [RUNNING], "init")
    assert done.returncode == 1
    assert "is inside the repository but not gitignored; refusing to write there." in done.stderr
    assert not (tree / ".config").exists() and calls(log) == []


def test_init_removes_its_password_when_the_repository_is_not_created_on_the_host(tree: Path, tmp_path: Path) -> None:
    (tree / ".gitignore").write_text(".config/\ndata/\n")
    subprocess.run(["git", "init", "-q"], cwd=tree, check=True)
    rules: list[Rule] = [RUNNING, ("compose -f stacks/backup/compose.yaml run --rm -T restic init", 0, "")]  # restic says yes, nothing appears on the host
    done, _ = sh(tree, tmp_path, rules, "init")
    assert done.returncode == 1
    assert "repository was not created on the host." in done.stderr
    assert not (tree / ".config" / "restic-password").exists()


def test_backup_stops_a_running_stack_saves_it_checks_and_restarts_it(tree: Path, tmp_path: Path) -> None:
    with_repository(tree)
    (tree / "stacks" / "actual" / ".env").write_text("A=1\n")
    rules: list[Rule] = [
        ("compose ps -q", 0, "abc123"),
        ("compose stop", 0, ""),
        ("compose start", 0, ""),
        ("compose -f stacks/backup/compose.yaml run --rm -T --user 1000:1000 -v nexahome-actual_data:/data/nexahome-actual_data:ro restic backup --tag stack=actual /data /stacks/actual/.env", 0, ""),
        ("compose -f stacks/backup/compose.yaml run --rm -T restic check", 0, ""),
        *LABELLED,
    ]
    done, log = sh(tree, tmp_path, rules, "backup")
    assert done.returncode == 0, done.stderr
    assert "stopping actual for a consistent copy" in done.stdout and "backing up actual" in done.stdout
    assert done.stdout.splitlines()[-1].startswith("backup ok: 1 stack(s) saved, repository checked, ")
    steps = {"|compose stop": "stop", "|compose start": "start", " restic backup ": "backup", " restic check": "check"}
    order = [name for c in calls(log) for key, name in steps.items() if key in c or c.endswith(key)]
    assert order == ["stop", "backup", "start", "check"], calls(log)


def test_a_failed_backup_still_restarts_the_stack_it_stopped(tree: Path, tmp_path: Path) -> None:
    with_repository(tree)
    rules: list[Rule] = [
        ("compose ps -q", 0, "abc123"),
        ("compose stop", 0, ""),
        ("compose start", 0, ""),
        ("compose -f stacks/backup/compose.yaml run --rm -T --user * restic backup *", 1, ""),
        *LABELLED,
    ]
    done, log = sh(tree, tmp_path, rules, "backup", "actual")
    assert done.returncode != 0
    assert "actual|compose start" in calls(log)


@pytest.mark.parametrize(
    ("snapshot_ages_in_days", "verdict"),
    [
        (None, "backup: no repository at {dir}"),
        ([], "backup: repository has no snapshots yet"),
        ([30, 2], "backup: last snapshot within 7 days"),
        ([30, 8], "backup: last snapshot OLDER than 7 days"),
    ],
)
def test_status_verdict_matches_the_package(tree: Path, tmp_path: Path, snapshot_ages_in_days: list[int] | None, verdict: str) -> None:
    """`make status` and `nexahome status` must give the same verdict (the second line, the size, is rounded differently by `du`)."""
    repository = tree / "data" / "backup"
    if snapshot_ages_in_days is not None:
        repository = with_repository(tree)
    now = time.time()
    for n, days in enumerate(snapshot_ages_in_days or []):
        snapshot = repository / "snapshots" / f"s{n}"
        snapshot.write_text("x")
        os.utime(snapshot, (now - days * DAY, now - days * DAY))
    done, log = sh(tree, tmp_path, [], "status")
    assert done.returncode == 0 and calls(log) == []  # status never calls docker
    expected = verdict.format(dir=repository)
    script_lines = done.stdout.splitlines()
    assert script_lines[0].split(" (")[0] == expected
    package_lines = backup_info.summary(repository, now, clone=True)
    assert package_lines[0].split(" (")[0] == expected
    if snapshot_ages_in_days is not None:
        assert script_lines[1].startswith("backup: repository size ") and f" in {repository}" in script_lines[1]
