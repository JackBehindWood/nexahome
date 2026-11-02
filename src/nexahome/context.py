"""Everything a command needs from the outside world, passed in so tests can replace it."""

import os
import sys
from collections.abc import Mapping
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

    @classmethod
    def default(cls) -> "Context":
        return cls(host=current(), runner=SubprocessRunner(), env=dict(os.environ), cwd=Path.cwd())
