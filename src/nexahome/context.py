"""Everything a command needs from the outside world, passed in so tests can replace it."""

import os
import shutil
import sys
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import TextIO

from nexahome.platform import Host, current
from nexahome.runner import Runner, SubprocessRunner


@dataclass
class Context:
    host: Host
    runner: Runner
    env: Mapping[str, str]  # the only place NEXAHOME_* variables are read from
    cwd: Path
    out: TextIO = field(default_factory=lambda: sys.stdout)
    err: TextIO = field(default_factory=lambda: sys.stderr)
    disk_free: Callable[[Path], int] = lambda path: shutil.disk_usage(path).free

    def checkout(self) -> Path | None:
        """The nearest parent of the working directory that looks like a NexaHome checkout, else None."""
        for directory in (self.cwd, *self.cwd.parents):
            if (directory / "stacks").is_dir() and (directory / "Makefile").is_file():
                return directory
        return None

    @classmethod
    def default(cls) -> "Context":
        return cls(host=current(), runner=SubprocessRunner(), env=dict(os.environ), cwd=Path.cwd())
