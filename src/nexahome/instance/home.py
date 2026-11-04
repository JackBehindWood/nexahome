"""Which folder is the NexaHome instance? One answer for every command (like git finding `.git`)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from nexahome.instance import CONFIG_NAME

if TYPE_CHECKING:
    from pathlib import Path

DEFAULT_NAME = "nexahome"  # under the home directory, which the Colima VM mounts


def stacks_dir(instance: Path) -> Path:
    """Where the stacks of an instance are. The one place that spells the layout."""
    return instance / "stacks"


def stack_dir(instance: Path, name: str) -> Path:
    return stacks_dir(instance) / name


def has_makefile(directory: Path) -> bool:
    """A git clone, or anything `make` can drive (an instance made by `nexahome init` has no Makefile)."""
    return (directory / "Makefile").is_file()


def has_settings(directory: Path) -> bool:
    """Made by `nexahome init`: it holds nexahome.toml, which names the stacks this host runs."""
    return (directory / CONFIG_NAME).is_file()


def is_instance(directory: Path) -> bool:
    """An instance made by `nexahome init` (holds nexahome.toml) or a git clone (stacks/ and a Makefile)."""
    return has_settings(directory) or (stacks_dir(directory).is_dir() and has_makefile(directory))


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
    return default if has_settings(default) else None
