"""Everything a command needs from the outside world, passed in so tests can replace it."""

import os
import shlex
import shutil
import sys
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import TextIO

from nexahome.errors import NexaHomeError
from nexahome.net import Fetcher, http_get
from nexahome.platform import Host, current
from nexahome.runner import Runner, SubprocessRunner


def ask_on_terminal(question: str) -> bool | None:
    """Ask a yes/no question. None means nobody can be asked (input is not a terminal)."""
    if not sys.stdin.isatty():
        return None
    try:
        return input(question).strip().lower() in ("y", "yes")
    except EOFError:
        return False


@dataclass
class Context:
    host: Host
    runner: Runner
    env: Mapping[str, str]  # the only place NEXAHOME_* variables are read from
    cwd: Path
    out: TextIO = field(default_factory=lambda: sys.stdout)
    err: TextIO = field(default_factory=lambda: sys.stderr)
    disk_free: Callable[[Path], int] = lambda path: shutil.disk_usage(path).free
    now: Callable[[], float] = time.time
    fetch: Fetcher = http_get  # network access, used by `update` only
    ask: Callable[[str], bool | None] = ask_on_terminal

    def checkout(self) -> Path | None:
        """The NexaHome checkout: $NEXAHOME_HOME if set, else the nearest parent of the working directory
        that holds stacks/ and a Makefile. None when there is none."""
        home = self.env.get("NEXAHOME_HOME")
        start = (self.cwd / home) if home else self.cwd
        for directory in (start, *start.parents):
            if (directory / "stacks").is_dir() and (directory / "Makefile").is_file():
                return directory
            if home:
                break  # an explicit setting is not searched upwards
        return None

    def require_checkout(self) -> Path:
        checkout = self.checkout()
        if checkout is None:
            if self.env.get("NEXAHOME_HOME"):
                raise NexaHomeError("NEXAHOME_HOME does not point at a NexaHome checkout (stacks/ and a Makefile)", 'ls "$NEXAHOME_HOME/stacks"')
            raise NexaHomeError(
                "not inside a NexaHome checkout (a folder that holds stacks/ and a Makefile)", "cd /path/to/nexahome"
            )
        return checkout

    def display(self, path: Path) -> str:
        """A path for a message or command line: relative to the working directory when inside it."""
        try:
            return shlex.quote(str(path.relative_to(self.cwd)))
        except ValueError:
            return shlex.quote(str(path))

    @classmethod
    def default(cls) -> "Context":
        return cls(host=current(), runner=SubprocessRunner(), env=dict(os.environ), cwd=Path.cwd())
