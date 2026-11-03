"""The personal-data scan (ported from scripts/check_personal_data.py, PK5; parity was proven before it was deleted)."""

from pathlib import Path

import pytest

from nexahome.policy.personal_data import load_denylist, scan_files, scan_text

# Built at run time so that this file does not trip the check it tests.
FLAGGED = "\n".join(
    [
        "clean line",
        "server at " + "192.168" + ".1.5",
        "gateway " + "10." + "0.0.1 and " + "172.16" + ".4.4",
        "public 8.8.8.8 is fine",
        "path " + "/Users/" + "alice/project",
        "path " + "/home/" + "bob",
        "host " + "printer" + ".local",
        "notes" + ".local.md is allowed",
        "allowed " + "192.168" + ".0.9 personal-data: ok",
        "has Secret-Term inside",
        "",
    ]
)


def test_flagged_clean_binary_and_missing_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".personal-denylist").write_text("# a comment\n\nsecret-term\n")
    (tmp_path / "flagged.txt").write_text(FLAGGED)
    (tmp_path / "clean.txt").write_text("nothing to see\n")
    (tmp_path / "binary.bin").write_bytes(b"\xff\xfe\x00")
    names = ["flagged.txt", "clean.txt", "binary.bin", "missing.txt"]
    assert scan_files(names) == [  # recorded from the original script's output; binary and missing files are skipped
        "flagged.txt:2: private IPv4 address",
        "flagged.txt:3: private IPv4 address",
        "flagged.txt:5: home directory path with a user name",
        "flagged.txt:6: home directory path with a user name",
        "flagged.txt:7: local hostname",
        "flagged.txt:10: term from .personal-denylist",
    ]


def test_a_clean_file_has_no_findings(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "clean.txt").write_text("nothing to see\n")
    assert scan_files(["clean.txt"]) == []


def test_each_rule_names_its_reason() -> None:
    reasons = [f.split(": ", 1)[1] for f in scan_text("f", FLAGGED, ["secret-term"])]
    assert reasons == [
        "private IPv4 address",  # one finding per rule and line, even with two addresses on it
        "private IPv4 address",
        "home directory path with a user name",
        "home directory path with a user name",
        "local hostname",
        "term from .personal-denylist",
    ]


def reasons_for(line: str) -> list[str]:
    return [f.split(": ", 1)[1] for f in scan_text("f", line)]


@pytest.mark.parametrize(
    ("line", "reason"),
    [
        ("mail " + "jo" + "@" + "example.org please", "email address"),
        ("host " + "nas" + ".lan", "home network hostname"),
        ("host " + "nas" + ".home.arpa", "home network hostname"),
        ("path " + "C:" + "\\Users\\" + "alice", "Windows home directory path with a user name"),
        ("path " + "C:" + "/Users/" + "alice", "Windows home directory path with a user name"),
    ],
)
def test_p08_patterns_are_flagged(line: str, reason: str) -> None:
    assert reason in reasons_for(line)  # a forward-slash Windows path also matches the Unix rule


@pytest.mark.parametrize(
    "line",
    [
        "Co-Authored-By: Claude <" + "noreply" + "@" + "anthropic.com>",
        "ID+handle" + "@" + "users.noreply.github.com",
        "uses: actions/checkout" + "@" + "v4.1.1",
        "image: x/y" + "@" + "sha256:" + "a" * 64,
        "mail " + "jo" + "@" + "example.org personal-data: ok",
        "a decorator " + "@" + "cache and user" + "@" + "host",
    ],
)
def test_p08_leaves_published_addresses_and_lookalikes_alone(line: str) -> None:
    assert reasons_for(line) == []


def test_denylist_ignores_comments_and_blank_lines(tmp_path: Path) -> None:
    path = tmp_path / "deny"
    path.write_text("# c\n\n Term One \n")
    assert load_denylist(path) == ["term one"]
    assert load_denylist(tmp_path / "absent") == []


def test_the_hook_entry_prints_findings_and_sets_the_exit_code(tmp_path: Path) -> None:
    import subprocess
    import sys

    (tmp_path / "flagged.txt").write_text(FLAGGED)
    (tmp_path / "clean.txt").write_text("nothing to see\n")
    run = lambda *names: subprocess.run(  # noqa: E731
        [sys.executable, "-m", "nexahome.policy.personal_data", *names], cwd=tmp_path, capture_output=True, text=True
    )
    flagged, clean = run("flagged.txt", "clean.txt"), run("clean.txt")
    assert (flagged.returncode, flagged.stdout.splitlines()) == (1, scan_text("flagged.txt", FLAGGED))
    assert (clean.returncode, clean.stdout) == (0, "")
