"""Start-up budget ("pay for what you use", ADR 0021): which modules a call imports is checked in a fresh process,
because the module list is what start-up time and memory are made of."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

HEAVY = {
    "dataclasses", "inspect", "json", "subprocess", "urllib", "urllib.request", "http.client", "ssl", "hashlib",
    "tempfile", "secrets", "random", "concurrent.futures", "shutil", "shlex", "importlib.metadata", "platform",
}
# argparse imports shutil (terminal width) and, on Python 3.14, dataclasses and inspect (via _colorize) as soon as a
# parser exists; that is the interpreter's cost, not ours
ARGPARSE_COST = {"dataclasses", "inspect", "shutil"} if sys.version_info >= (3, 14) else {"shutil"}
# what each call may NOT import (everything else it may)
BUDGET: dict[str, tuple[list[str], set[str]]] = {
    "--version": (["--version"], HEAVY | {"argparse", "nexahome.context", "nexahome.runner", "nexahome.commands.doctor", "nexahome.diagnosis"}),
    "--help": (["--help"], HEAVY - ARGPARSE_COST | {"nexahome.context", "nexahome.runner", "nexahome.diagnosis", "nexahome.updater", "nexahome.envfile", "nexahome.policy"}),
    "doctor --help": (["doctor", "--help"], HEAVY - ARGPARSE_COST | {"nexahome.diagnosis", "nexahome.commands.update", "nexahome.commands.env", "nexahome.updater"}),
    "doctor": (["doctor"], HEAVY - ARGPARSE_COST - {"subprocess", "concurrent.futures"} | {"nexahome.updater", "nexahome.commands.update", "nexahome.commands.env"}),
    "init --help": (["init", "--help"], HEAVY - ARGPARSE_COST | {"nexahome.instance.create", "nexahome.instance.bundle", "nexahome.docker", "nexahome.commands.doctor"}),
    "update --help": (["update", "--help"], HEAVY - ARGPARSE_COST | {"nexahome.updater", "nexahome.net", "nexahome.commands.doctor"}),
}


def modules_imported_by(arguments: list[str], tmp_path: Path) -> set[str]:
    code = (
        "import sys; from nexahome.cli import main; main(sys.argv[1:]); "
        "seen = sorted(sys.modules); import json; sys.stderr.write('\\n' + json.dumps(seen))"
    )
    empty = tmp_path / "no-programs"
    empty.mkdir(exist_ok=True)
    done = subprocess.run(
        [sys.executable, "-c", code, *arguments], capture_output=True, text=True, cwd=tmp_path, env={"PATH": str(empty)}, check=False
    )
    return set(json.loads(done.stderr.rsplit("\n", 1)[1]))


@pytest.mark.parametrize("name", BUDGET)
def test_a_call_imports_only_what_it_needs(name: str, tmp_path: Path) -> None:
    arguments, forbidden = BUDGET[name]
    assert sorted(modules_imported_by(arguments, tmp_path) & forbidden) == []


def test_importing_the_commands_package_loads_no_command(tmp_path: Path) -> None:
    code = "import sys, nexahome.commands as c; c.names(); print(sorted(m for m in sys.modules if m.startswith('nexahome.commands.')))"
    done = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=False)
    assert done.stdout.strip() == "[]"


def test_importing_the_package_does_nothing_else() -> None:
    code = "import sys; before = set(sys.modules); import nexahome; print(sorted(set(sys.modules) - before))"
    done = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=False)
    assert done.stdout.strip() == "['nexahome']"
