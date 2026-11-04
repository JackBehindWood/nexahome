"""The two `.env` creators side by side: the `make up` shell block (Makefile) and `nexahome.stacks.envfile.prepare` (S-21).

Both must stay equal until `nexahome up` replaces the Makefile block (PK7). Known differences are asserted as differences,
so a change on either side shows up here instead of in a user's `.env`. The Makefile is run unchanged in a scratch tree with
a stub `docker`; nothing real is read or written.
"""

import os
import re
import shutil
import stat
import subprocess
from collections.abc import Iterator
from pathlib import Path

import pytest

from nexahome.docker import EDGE_NETWORK, compose
from nexahome.stacks import envfile
from script_harness import REPO, calls, install_stub

pytestmark = pytest.mark.skipif(shutil.which("make") is None, reason="make is not installed")

SECRET = re.compile(r"[A-Za-z0-9]{48}")
EXAMPLE = "# comment\nA=GENERATE\nNAME=plain\nB=GENERATE\n"


@pytest.fixture(autouse=True)
def usual_umask() -> Iterator[None]:
    previous = os.umask(0o022)
    yield
    os.umask(previous)


def make_stack(root: Path, example: bytes, *, compose_text: str = "services: {}\n", env: str | None = None) -> Path:
    stack = root / "stacks" / "s"
    stack.mkdir(parents=True)
    (stack / "compose.yaml").write_text(compose_text)
    (stack / ".env.example").write_bytes(example)
    (stack / ".env.example").chmod(0o644)
    if env is not None:
        (stack / ".env").write_text(env)
    return stack


def run_make(root: Path, bin_dir: Path) -> subprocess.CompletedProcess[str]:
    """`make up STACK=s` as a user runs it, from a copy of the real Makefile."""
    shutil.copy(REPO / "Makefile", root / "Makefile")
    env = {**os.environ, "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}"}
    return subprocess.run(["make", "--no-print-directory", "up", "STACK=s"], cwd=root, env=env, capture_output=True, text=True, timeout=60, check=False)


class Both:
    """The same `.env.example` prepared by the Makefile in one folder and by the package in another."""

    def __init__(self, tmp_path: Path, example: bytes, *, env: str | None = None, compose_text: str = "services: {}\n") -> None:
        self.make_root, self.package_root = tmp_path / "make", tmp_path / "package"
        self.make_stack = make_stack(self.make_root, example, env=env, compose_text=compose_text)
        self.package_stack = make_stack(self.package_root, example, env=env, compose_text=compose_text)
        self.bin_dir = tmp_path / "bin"
        self.docker_log = install_stub(self.bin_dir, "docker", [("*", 0, "")])
        self.done = run_make(self.make_root, self.bin_dir)
        self.result = envfile.prepare(self.package_stack)

    def text(self, which: str) -> str:
        return ((self.make_stack if which == "make" else self.package_stack) / ".env").read_bytes().decode()

    def mode(self, which: str) -> int:
        return stat.S_IMODE(((self.make_stack if which == "make" else self.package_stack) / ".env").stat().st_mode)


def test_both_fill_every_generate_line_with_a_48_character_secret_and_keep_the_rest(tmp_path: Path) -> None:
    both = Both(tmp_path, EXAMPLE.encode())
    assert both.done.returncode == 0, both.done.stderr
    for which in ("make", "package"):
        lines = both.text(which).splitlines()
        assert lines[:1] == ["# comment"] and lines[2] == "NAME=plain"
        assert [bool(SECRET.fullmatch(lines[i].split("=", 1)[1])) for i in (1, 3)] == [True, True], which
        assert lines[1].startswith("A=") and lines[3].startswith("B=")
    assert both.text("make").split("=")[1] != both.text("make").split("=")[3]  # two secrets, not one repeated
    assert "generated secrets in stacks/s/.env (not shown)" in both.done.stdout
    assert both.result is not None and both.result.generated == ("A", "B")
    assert both.result.created and "created stacks/s/.env from .env.example" in both.done.stdout


@pytest.mark.parametrize("example", [b"A=GENERATE\nNAME=plain\n", b"X=1\n"])
def test_both_stop_at_a_change_me_value_and_name_the_same_keys_without_generating(tmp_path: Path, example: bytes) -> None:
    example = example + b"TOKEN=CHANGE_ME\nOTHER=CHANGE_ME_TOO\n"
    both = Both(tmp_path, example)
    assert both.done.returncode != 0  # make reports the recipe's exit 1 as its own status
    listed = [line.strip() for line in both.done.stdout.splitlines() if line.startswith("  ")]
    assert both.result is not None and list(both.result.pending) == listed == ["TOKEN", "OTHER"]
    assert both.text("make") == both.text("package") == example.decode()  # nothing generated while a value is open


def test_both_leave_an_existing_env_alone(tmp_path: Path) -> None:
    both = Both(tmp_path, b"A=GENERATE\n", env="A=mine\nB=2\n")
    assert both.done.returncode == 0
    assert both.text("make") == both.text("package") == "A=mine\nB=2\n"
    assert both.result is not None and not both.result.created and both.result.generated == ()
    assert "created" not in both.done.stdout


def test_both_fill_a_generate_line_added_to_an_existing_env(tmp_path: Path) -> None:
    both = Both(tmp_path, b"unused=1\n", env="A=GENERATE\nB=2\n")
    for which in ("make", "package"):
        first, second = both.text(which).splitlines()
        assert SECRET.fullmatch(first.removeprefix("A=")) and second == "B=2", which


def test_known_difference_the_mode_of_an_env_without_generated_secrets(tmp_path: Path) -> None:
    """The Makefile copies the example (mode from the umask, here 644); the package always writes 600. Finding S-21b."""
    plain = Both(tmp_path / "plain", b"A=1\n")
    assert (plain.mode("make"), plain.mode("package")) == (0o644, 0o600)
    generated = Both(tmp_path / "generated", b"A=GENERATE\n")
    assert (generated.mode("make"), generated.mode("package")) == (0o600, 0o600)  # the Makefile rewrite runs under umask 077


def test_known_difference_a_crlf_generate_line(tmp_path: Path) -> None:
    """The Makefile matches `=GENERATE` at the very end of the line, so CRLF files are left as they are; the package reads text lines and generates. Finding S-21c."""
    both = Both(tmp_path, b"A=GENERATE\r\nB=2\r\n")
    assert both.text("make") == "A=GENERATE\r\nB=2\r\n"
    assert SECRET.fullmatch(both.text("package").splitlines()[0].removeprefix("A="))


def test_known_difference_a_missing_final_newline(tmp_path: Path) -> None:
    """The Makefile loop ends every line with a newline; the package keeps the file as written."""
    both = Both(tmp_path, b"A=GENERATE\nNAME=plain")
    assert both.text("make").endswith("NAME=plain\n") and both.text("package").endswith("NAME=plain")


def test_known_difference_the_network_and_the_start_line(tmp_path: Path) -> None:
    """Same name and same `up -d --wait`; the Makefile makes the network only for a stack that declares it, `nexahome env` prints the line for every instance. Finding S-21d."""
    assert EDGE_NETWORK == "nexahome-edge" and re.search(rf"^EDGE_NET := {EDGE_NETWORK}$", (REPO / "Makefile").read_text(), re.M)
    plain = Both(tmp_path / "plain", b"A=1\n")
    assert [c for c in calls(plain.docker_log) if "network" in c] == []
    assert calls(plain.docker_log) == ["s|compose up -d --wait"] and compose.up_command("s").endswith(" up -d --wait")
    edge = Both(tmp_path / "edge", b"A=1\n", compose_text=f"networks:\n  edge:\n    name: {EDGE_NETWORK}\n")
    assert calls(edge.docker_log)[0] == f"make|network inspect {EDGE_NETWORK}"
    assert compose.network_command() == f"docker network inspect {EDGE_NETWORK} >/dev/null 2>&1 || docker network create {EDGE_NETWORK}"
