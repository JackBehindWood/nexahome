"""Golden parity (PK-C3): the port prints exactly what scripts/check_personal_data.py prints."""

from pathlib import Path

import pytest

from nexahome.policy.personal_data import load_denylist, scan_files, scan_text

from conftest import load_script

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


def test_matches_the_original_on_flagged_clean_binary_and_missing_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".personal-denylist").write_text("# a comment\n\nsecret-term\n")
    (tmp_path / "flagged.txt").write_text(FLAGGED)
    (tmp_path / "clean.txt").write_text("nothing to see\n")
    (tmp_path / "binary.bin").write_bytes(b"\xff\xfe\x00")
    names = ["flagged.txt", "clean.txt", "binary.bin", "missing.txt"]
    original = load_script("check_personal_data")
    code = original.main(names)
    assert capsys.readouterr().out.splitlines() == scan_files(names)
    assert code == 1


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


def test_denylist_ignores_comments_and_blank_lines(tmp_path: Path) -> None:
    path = tmp_path / "deny"
    path.write_text("# c\n\n Term One \n")
    assert load_denylist(path) == ["term one"]
    assert load_denylist(tmp_path / "absent") == []
