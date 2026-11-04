"""What `nexahome init` does: copy the bundled stacks into a new folder and write its settings.

Never overwrites: the target must be new or empty, and every file is created exclusively. Writes no secret and no
`.env` (`nexahome env` does that, mode 600). Needs no network and extracts no archive: files are read from the
installed package. If a write fails, only what this run created is removed.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple

from nexahome import files
from nexahome.defaults import DEFAULT_STACKS, ENV_HOME, PUBLIC_FILE_MODE, STACK_FILE_MAX_BYTES
from nexahome.errors import NexaHomeError
from nexahome.instance import CONFIG_NAME, REINSTALL, bundle, config, home, manifest

if TYPE_CHECKING:
    from nexahome.context import Context



class Created(NamedTuple):
    root: Path
    stacks: tuple[str, ...]  # every stack copied
    enabled: tuple[str, ...]  # the ones nexahome.toml lists
    files: int


def target(ctx: Context, directory: str | None) -> Path:
    """DIR, else --home or $NEXAHOME_HOME, else ~/nexahome, as an absolute path."""
    chosen = directory or ctx.env.get(ENV_HOME)
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


def create(root: Path, source: Path, version: str) -> Created:
    """Copy `source` (the stacks) to root/stacks and write nexahome.toml and the manifest. `root` must have passed
    refuse_unless_new."""
    import hashlib

    directories, paths = bundle.walk(source)
    stacks = tuple(sorted(name for name in directories if "/" not in name))
    if DEFAULT_STACKS[0] not in stacks:
        raise NexaHomeError("this install's bundled stacks do not include the demo stack", REINSTALL)
    created: list[Path] = []
    hashes: dict[str, str] = {}
    try:
        files.make_directory(root / "stacks", created)
        for name in directories:
            files.make_directory(root / "stacks" / name, created)
        for name in paths:
            if (source / name).stat().st_size > STACK_FILE_MAX_BYTES:
                raise NexaHomeError(f"{name} is larger than {STACK_FILE_MAX_BYTES} bytes", REINSTALL)
            data = (source / name).read_bytes()
            files.create_exclusive(root / "stacks" / name, data, PUBLIC_FILE_MODE, created)
            hashes[f"stacks/{name}"] = hashlib.sha256(data).hexdigest()
        files.create_exclusive(root / CONFIG_NAME, config.render(DEFAULT_STACKS).encode(), PUBLIC_FILE_MODE, created)
        files.make_directory(root / ".nexahome", created)
        files.create_exclusive(root / manifest.PATH, manifest.render(version, hashes).encode(), PUBLIC_FILE_MODE, created)
    except OSError as error:
        files.remove_created(created)
        raise NexaHomeError(f"init stopped and removed what it had made: {error}", f"nexahome init {root}") from error
    except BaseException:
        files.remove_created(created)
        raise
    return Created(root, stacks, DEFAULT_STACKS, len(paths))
