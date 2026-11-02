"""How recent the backup is, read from the repository folder (port of `backup.sh status`; read-only)."""

from collections.abc import Mapping
from pathlib import Path

from nexahome import envfile

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
    if not (directory / "config").is_file():
        return [f"backup: no repository at {directory} (make backup-init)"]
    snapshots = [f for f in (directory / "snapshots").rglob("*") if f.is_file()]
    if any(now - f.stat().st_mtime < RECENT_SECONDS for f in snapshots):
        first = "backup: last snapshot within 7 days"
    elif snapshots:
        first = "backup: last snapshot OLDER than 7 days (make backup)"
    else:
        first = "backup: repository has no snapshots yet (make backup)"
    size = sum(f.stat().st_size for f in directory.rglob("*") if f.is_file())
    return [first, f"backup: repository size {human_size(size)} in {directory}"]
