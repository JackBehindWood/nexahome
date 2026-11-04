"""Creating and replacing files: the one place that sets a file's mode, refuses to overwrite and never leaves a half-written file.

Secrets (`.env`, mode 600) and shared files (mode 644) both pass through here, so the rules cannot drift apart.
`created` lists record what one run made, so a failed run can remove exactly that (`remove_created`).
"""

from __future__ import annotations

import os
from pathlib import Path

from nexahome.defaults import PUBLIC_DIR_MODE


def make_directory(path: Path, created: list[Path]) -> None:
    """Create `path` and any missing parents, recording each one so a failure can remove them."""
    missing: list[Path] = []
    for folder in (path, *path.parents):
        if folder.exists():
            break
        missing.append(folder)
    for folder in reversed(missing):
        folder.mkdir()
        created.append(folder)
        os.chmod(folder, PUBLIC_DIR_MODE)


def create_exclusive(path: Path, data: bytes, mode: int, created: list[Path] | None = None) -> None:
    """Create `path` with exactly `mode` (whatever the umask) and write `data`. Never overwrites: an existing file
    raises FileExistsError. The path is recorded in `created` once it exists."""
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
    if created is not None:
        created.append(path)
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(data)
    os.chmod(path, mode)


def replace_atomically(path: Path, text: str, mode: int) -> None:
    """Replace `path` with `text`, all or nothing: the text is written to a file beside it and renamed over it."""
    import tempfile  # only a run that rewrites a file pays for it

    descriptor, temporary = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name.lstrip('.')}.")
    try:
        with os.fdopen(descriptor, "w") as handle:
            handle.write(text)
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise


def remove_created(created: list[Path]) -> None:
    """Remove what `created` lists, newest first. Best effort: what is left is named in the error message."""
    for path in reversed(created):
        try:
            path.unlink() if path.is_file() else path.rmdir()
        except OSError:
            pass
