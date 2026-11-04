"""Run the repository's shell scripts in a scratch copy with stub commands first on PATH.

The scripts under test are copied unchanged. They `cd` to the folder above their own, so the copy is isolated:
nothing in the real checkout is read or written. A stub prints canned output for the argument lists it is given,
logs every call as `<folder>|<arguments>`, and exits 1 for anything else.
"""

import os
import shlex
import shutil
import stat
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "scripts"

# A stub rule: (argument pattern with * as the wildcard, exit code, stdout).
Rule = tuple[str, int, str]

# Variables the scripts read; a developer's shell must not leak into a test.
_SCRIPT_VARIABLES = ("WAIT", "VERBOSE", "SNAPSHOT", "TARGET", "READ", "EDITOR")


def make_tree(root: Path, scripts: tuple[str, ...]) -> Path:
    """A scratch checkout holding only the named scripts."""
    tree = root / "tree"
    (tree / "scripts").mkdir(parents=True)
    for name in scripts:
        shutil.copy(SCRIPTS / name, tree / "scripts" / name)
    return tree


def _shell_pattern(pattern: str) -> str:
    return "*".join(shlex.quote(piece) if piece else "" for piece in pattern.split("*"))


def install_stub(bin_dir: Path, name: str, rules: list[Rule]) -> Path:
    """Write `bin_dir/name`; returns its call log. The first matching rule wins."""
    bin_dir.mkdir(parents=True, exist_ok=True)
    log = bin_dir / f"{name}-calls.log"
    lines = ["#!/bin/sh", f'printf "%s|%s\\n" "${{PWD##*/}}" "$*" >> {shlex.quote(str(log))}', 'case "$*" in']
    for pattern, code, out in rules:
        body = f"printf '%s\\n' {shlex.quote(out)}; " if out else ""
        lines.append(f"  {_shell_pattern(pattern)}) {body}exit {code};;")
    lines += ["  *) exit 1;;", "esac", ""]
    script = bin_dir / name
    script.write_text("\n".join(lines))
    script.chmod(script.stat().st_mode | stat.S_IXUSR)
    log.touch()
    return log


def calls(log: Path) -> list[str]:
    return log.read_text().splitlines()


def run_script(
    tree: Path, name: str, *args: str, bin_dir: Path | None = None, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    """`sh scripts/<name> args` from the tree, as the Makefile runs it, with stubs first on PATH."""
    full = {k: v for k, v in os.environ.items() if not k.startswith("NEXAHOME_") and k not in _SCRIPT_VARIABLES}
    if bin_dir is not None:
        full["PATH"] = f"{bin_dir}{os.pathsep}{full['PATH']}"
    full.update(env or {})
    return subprocess.run(["sh", f"scripts/{name}", *args], cwd=tree, env=full, capture_output=True, text=True, timeout=60, check=False)
