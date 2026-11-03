"""What `nexahome init` does: copy the bundled stacks into a new folder and write its settings.

Never overwrites: the target must be new or empty, and every file is created exclusively. Writes no secret and no
`.env` (`nexahome env` does that, mode 600). Needs no network and extracts no archive: files are read from the
installed package. If a write fails, only what this run created is removed.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple

from nexahome.errors import NexaHomeError
from nexahome.instance import CONFIG_NAME, bundle, config, home, manifest

if TYPE_CHECKING:
    from nexahome.context import Context

FILE_MODE = 0o644  # package files are not secret, and a container user must be able to read them whatever the umask
DIR_MODE = 0o755


class Created(NamedTuple):
    root: Path
    stacks: tuple[str, ...]  # every stack copied
    enabled: tuple[str, ...]  # the ones nexahome.toml lists
    files: int


def target(ctx: Context, directory: str | None) -> Path:
    """DIR, else --home or $NEXAHOME_HOME, else ~/nexahome, as an absolute path."""
    chosen = directory or ctx.env.get("NEXAHOME_HOME")
    return Path(os.path.abspath(ctx.cwd / chosen if chosen else ctx.host.home / home.DEFAULT_NAME))


def refuse_unless_new(path: Path) -> None:
    """Raise unless `path` can take a new instance: inside no clone or instance, not a file, empty or missing."""
    for parent in (path, *path.parents):
        if home.is_instance(parent):
            if (parent / "Makefile").is_file() and not (parent / CONFIG_NAME).is_file():
                raise NexaHomeError(f"{path} is inside a NexaHome clone; init is for a folder of your own", "git pull --ff-only")
            where = "is already a NexaHome instance" if parent == path else f"is inside a NexaHome instance ({parent}); instances do not nest"
            raise NexaHomeError(f"{path} {where}", "nexahome init ~/nexahome-new")
    if path.exists() and not path.is_dir():
        raise NexaHomeError(f"{path} is a file, not a folder", "nexahome init ~/nexahome-new")
    if path.is_dir() and any(path.iterdir()):
        raise NexaHomeError(f"{path} is not empty; init never overwrites", "nexahome init ~/nexahome-new")


def _make_directory(path: Path, created: list[Path]) -> None:
    """Create `path` and any missing parents, recording each one so a failure can remove them."""
    missing: list[Path] = []
    for folder in (path, *path.parents):
        if folder.exists():
            break
        missing.append(folder)
    for folder in reversed(missing):
        folder.mkdir()
        created.append(folder)
        os.chmod(folder, DIR_MODE)


def _write(path: Path, data: bytes, created: list[Path]) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, FILE_MODE)
    created.append(path)
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(data)
    os.chmod(path, FILE_MODE)


def _remove(created: list[Path]) -> None:
    for path in reversed(created):
        try:
            path.unlink() if path.is_file() else path.rmdir()
        except OSError:
            pass  # best effort: what is left is named in the message


def create(root: Path, source: Path, version: str) -> Created:
    """Copy `source` (the stacks) to root/stacks and write nexahome.toml and the manifest. `root` must have passed
    refuse_unless_new."""
    import hashlib

    directories, files = bundle.walk(source)
    stacks = tuple(sorted(name for name in directories if "/" not in name))
    if config.DEFAULT_STACKS[0] not in stacks:
        raise NexaHomeError("this install's bundled stacks do not include the demo stack", "uv tool install --reinstall nexahome")
    created: list[Path] = []
    hashes: dict[str, str] = {}
    try:
        _make_directory(root / "stacks", created)
        for name in directories:
            _make_directory(root / "stacks" / name, created)
        for name in files:
            if (source / name).stat().st_size > bundle.MAX_FILE_BYTES:
                raise NexaHomeError(f"{name} is larger than {bundle.MAX_FILE_BYTES} bytes", "uv tool install --reinstall nexahome")
            data = (source / name).read_bytes()
            _write(root / "stacks" / name, data, created)
            hashes[f"stacks/{name}"] = hashlib.sha256(data).hexdigest()
        _write(root / CONFIG_NAME, config.render(config.DEFAULT_STACKS).encode(), created)
        _make_directory(root / ".nexahome", created)
        _write(root / manifest.PATH, manifest.render(version, hashes).encode(), created)
    except OSError as error:
        _remove(created)
        raise NexaHomeError(f"init stopped and removed what it had made: {error}", f"nexahome init {root}") from error
    except BaseException:
        _remove(created)
        raise
    return Created(root, stacks, config.DEFAULT_STACKS, len(files))
