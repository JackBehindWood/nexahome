"""How recent the backup is, read from the repository folder (port of `backup.sh status`; read-only)."""

import os
from collections.abc import Mapping
from pathlib import Path

from nexahome.stacks import envfile

RECENT_SECONDS = 7 * 24 * 3600
_UNITS = ("B", "K", "M", "G", "T")


def repository_dir(checkout: Path, env: Mapping[str, str]) -> Path:
    """stacks/backup/.env wins, then $NEXAHOME_BACKUP_DIR, then data/backup (as backup.sh does)."""
    value = None
    try:
        value = envfile.read_value((checkout / "stacks" / "backup" / ".env").read_text(), "NEXAHOME_BACKUP_DIR")
    except OSError:
        pass
    chosen = value or env.get("NEXAHOME_BACKUP_DIR")
    return Path(chosen) if chosen else checkout / "data" / "backup"


def human_size(size: float) -> str:
    unit = 0
    while size >= 1024 and unit < len(_UNITS) - 1:
        size /= 1024
        unit += 1
    return f"{size:.0f}B" if unit == 0 else f"{size:.1f}{_UNITS[unit]}"


def summary(directory: Path, now: float) -> list[str]:
    """Lines for `nexahome status`: whether the newest snapshot is under 7 days old, and the repository size, from one walk of the folder."""
    if not (directory / "config").is_file():
        return [f"backup: no repository at {directory} (make backup-init)"]
    size = 0
    newest: float | None = None  # modification time of the newest snapshot file; None if there is none
    snapshots = directory / "snapshots"
    for folder, _, files in os.walk(directory):  # one pass, constant memory however big the repository is
        in_snapshots = Path(folder) == snapshots or snapshots in Path(folder).parents
        for name in files:
            info = os.stat(os.path.join(folder, name))
            size += info.st_size
            if in_snapshots and (newest is None or info.st_mtime > newest):
                newest = info.st_mtime
    if newest is not None and now - newest < RECENT_SECONDS:
        first = "backup: last snapshot within 7 days"
    elif newest is not None:
        first = "backup: last snapshot OLDER than 7 days (make backup)"
    else:
        first = "backup: repository has no snapshots yet (make backup)"
    return [first, f"backup: repository size {human_size(size)} in {directory}"]
