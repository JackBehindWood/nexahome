"""The stacks that ship inside the package: where they are and which files of them an instance gets.

The wheel carries `stacks/` as `nexahome/_stacks` (pyproject.toml). A development install or an sdist test run has no
such folder, so the repository's own `stacks/` stands in; the same filter applies to both, which keeps a local
`.env` or key of a developer out of an instance.
"""

from __future__ import annotations

import os
from pathlib import Path

SKIP_NAMES = frozenset({"README.md", ".env", "data", "__pycache__"})  # READMEs stay on GitHub (their links break here)
TEMPLATE_README = ("_template", "README.md")  # the one README that ships: `nexahome stacks new` copies it (it has no links)
SECRET_SUFFIXES = (".pem", ".key", ".p12", ".kdbx")


def location() -> Path | None:
    """The folder that holds the stacks, or None when this install carries none."""
    package = Path(__file__).resolve().parents[1]
    shipped = package / "_stacks"
    if shipped.is_dir():
        return shipped
    repository = package.parents[1]  # src/nexahome -> the repository root
    if (repository / "src" / "nexahome").is_dir() and (repository / "stacks").is_dir():
        return repository / "stacks"
    return None


def wanted(name: str) -> bool:
    """False for files that never belong in an instance: READMEs, any `.env` except `.env.example`, keys, caches."""
    if name in SKIP_NAMES or name.endswith(SECRET_SUFFIXES) or name.endswith((".pyc", ".DS_Store")):
        return False
    return not (name.startswith(".env") and name != ".env.example")


def walk(root: Path) -> tuple[list[str], list[str]]:
    """(directories, files) under `root` as sorted `/`-separated relative paths, links not followed, filtered."""
    directories: list[str] = []
    files: list[str] = []
    for folder, names, filenames in os.walk(root, followlinks=False):
        names[:] = sorted(n for n in names if wanted(n))
        relative = Path(folder).relative_to(root)
        directories += [(relative / n).as_posix() for n in names]
        keep = [n for n in sorted(filenames) if wanted(n) or (relative.as_posix(), n) == TEMPLATE_README]
        files += [(relative / n).as_posix() for n in keep if not os.path.islink(os.path.join(folder, n))]
    return sorted(directories), sorted(files)
