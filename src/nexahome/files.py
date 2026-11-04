"""Creating and replacing files: the one place that sets a file's mode, refuses to overwrite and never leaves a half-written file.

Secrets (`.env`, mode 600) and shared files (mode 644) both pass through here, so the rules cannot drift apart.
`created` lists record what one run made, so a failed run can remove exactly that (`remove_created`).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

from nexahome.defaults import PUBLIC_DIR_MODE
from nexahome.errors import NexaHomeError

if TYPE_CHECKING:
    from types import TracebackType


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
    """Replace `path` with `text`, all or nothing: the text is written to a file beside it, flushed to disk, renamed
    over it, and the folder is flushed too, so a power cut leaves the old file or the new one, never an empty one
    (ADR 0016). `os.fsync` is the portable call; on macOS the drive may still hold the data in its own cache."""
    import tempfile  # only a run that rewrites a file pays for it

    descriptor, temporary = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name.lstrip('.')}.")
    try:
        with os.fdopen(descriptor, "w") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise
    try:  # the name is already in place; a filesystem that refuses to flush a folder must not fail the write
        folder = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(folder)
        finally:
            os.close(folder)
    except OSError:
        pass


def remove_created(created: list[Path]) -> None:
    """Remove what `created` lists, newest first. Best effort: what is left is named in the error message."""
    for path in reversed(created):
        try:
            path.unlink() if path.is_file() else path.rmdir()
        except OSError:
            pass


class Rollback:
    """`with Rollback(created, "init", fix):` around the writes of one run. On any error it removes what `created` lists;
    an OSError (disk full, no permission) becomes a NexaHomeError that names `what` and ends in `fix`; any other error
    passes through unchanged. A plain class, not `contextlib`, so no import is paid for."""

    __slots__ = ("created", "what", "fix")

    def __init__(self, created: list[Path], what: str, fix: str) -> None:
        self.created, self.what, self.fix = created, what, fix

    def __enter__(self) -> Rollback:
        return self

    def __exit__(self, kind: type[BaseException] | None, error: BaseException | None, trace: TracebackType | None) -> bool:
        if error is None:
            return False
        remove_created(self.created)
        if isinstance(error, OSError):
            raise NexaHomeError(f"{self.what} stopped and removed what it had made: {error}", self.fix) from error
        return False
