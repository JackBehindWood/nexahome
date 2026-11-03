"""Which folder is the NexaHome instance? One answer for every command (like git finding `.git`)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nexahome.instance import CONFIG_NAME

if TYPE_CHECKING:
    from pathlib import Path

DEFAULT_NAME = "nexahome"  # under the home directory, which the Colima VM mounts


def is_instance(directory: Path) -> bool:
    """An instance made by `nexahome init` (holds nexahome.toml) or a git clone (stacks/ and a Makefile)."""
    return (directory / CONFIG_NAME).is_file() or ((directory / "stacks").is_dir() and (directory / "Makefile").is_file())


def find(cwd: Path, explicit: str | None, user_home: Path) -> Path | None:
    """The instance, in order: `explicit` (--home or $NEXAHOME_HOME, relative to `cwd`, not searched upwards), the
    nearest parent of `cwd` that is one, else ~/nexahome when it holds nexahome.toml. None when there is none."""
    if explicit:
        start = cwd / explicit
        return start if is_instance(start) else None
    for directory in (cwd, *cwd.parents):
        if is_instance(directory):
            return directory
    default = user_home / DEFAULT_NAME
    return default if (default / CONFIG_NAME).is_file() else None
