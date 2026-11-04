"""How recent the backup is, read from the repository folder (port of `backup.sh status`; read-only)."""

import os
from collections.abc import Mapping
from pathlib import Path

from nexahome.defaults import BACKUP_RECENT_SECONDS, ENV_BACKUP_DIR
from nexahome.stacks import envfile

_UNITS = ("B", "K", "M", "G", "T")
_NO_BACKUP = "not available in an instance yet"


def repository_dir(instance: Path, env: Mapping[str, str]) -> Path:
    """stacks/backup/.env wins, then $NEXAHOME_BACKUP_DIR, then data/backup (as backup.sh does)."""
    value = None
    try:
        value = envfile.read_value((instance / "stacks" / "backup" / ".env").read_text(), ENV_BACKUP_DIR)
    except OSError:
        pass
    chosen = value or env.get(ENV_BACKUP_DIR)
    return Path(chosen) if chosen else instance / "data" / "backup"


def human_size(size: float) -> str:
    unit = 0
    while size >= 1024 and unit < len(_UNITS) - 1:
        size /= 1024
        unit += 1
    return f"{size:.0f}B" if unit == 0 else f"{size:.1f}{_UNITS[unit]}"


def summary(directory: Path, now: float, clone: bool) -> list[str]:
    """Lines for `nexahome status`: whether the newest snapshot is under 7 days old, and the repository size, from one walk of the folder.
    `clone` says the folder has the Makefile; an instance made by `nexahome init` cannot back up yet (PK7)."""
    if not (directory / "config").is_file():
        return [f"backup: no repository at {directory} ({'in a git clone: make backup-init' if clone else _NO_BACKUP})"]
    how = "in a git clone: make backup" if clone else _NO_BACKUP
    size = 0
    newest: float | None = None  # modification time of the newest snapshot file; None if there is none
    snapshots = directory / "snapshots"
    for folder, _, files in os.walk(directory):  # one pass, constant memory however big the repository is
        in_snapshots = Path(folder) == snapshots or snapshots in Path(folder).parents
        for name in files:
            try:
                info = os.stat(os.path.join(folder, name))
            except FileNotFoundError:  # a dangling link, or restic pruned the file while this walk ran
                continue
            size += info.st_size
            if in_snapshots and (newest is None or info.st_mtime > newest):
                newest = info.st_mtime
    if newest is not None and now - newest < BACKUP_RECENT_SECONDS:
        first = "backup: last snapshot within 7 days"
    elif newest is not None:
        first = f"backup: last snapshot OLDER than 7 days ({how})"
    else:
        first = f"backup: repository has no snapshots yet ({how})"
    return [first, f"backup: repository size {human_size(size)} in {directory}"]
