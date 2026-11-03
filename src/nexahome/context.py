"""Everything a command needs from the outside world, passed in so tests can replace it.

Heavy standard-library modules are imported inside the functions that use them, so a command that does not need
them does not pay for them (see tests/test_startup.py).
"""

from __future__ import annotations

import os
import sys
import time
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import TYPE_CHECKING, TextIO

from nexahome.errors import NexaHomeError
from nexahome.platform import Host, current
from nexahome.runner import Runner, SubprocessRunner

if TYPE_CHECKING:
    from nexahome.release.net import Downloader, Fetcher


def ask_on_terminal(question: str) -> bool | None:
    """Ask a yes/no question. None means nobody can be asked (input is not a terminal)."""
    if not sys.stdin.isatty():
        return None
    try:
        return input(question).strip().lower() in ("y", "yes")
    except EOFError:
        return False


def _disk_free(path: Path) -> int:
    import shutil

    return shutil.disk_usage(path).free


def _fetch(url: str, *, timeout: float, max_bytes: int) -> bytes:
    from nexahome.release.net import http_get  # the network code (urllib, ssl) is loaded only when a command fetches

    return http_get(url, timeout=timeout, max_bytes=max_bytes)


def _download(url: str, destination: Path, *, timeout: float, max_bytes: int) -> str:
    from nexahome.release.net import http_download

    return http_download(url, destination, timeout=timeout, max_bytes=max_bytes)


class Context:
    """Host facts and every outside dependency. Plain attributes, so a test can replace any of them."""

    __slots__ = ("host", "runner", "env", "cwd", "out", "err", "disk_free", "now", "fetch", "download", "ask")

    def __init__(
        self,
        host: Host,
        runner: Runner,
        env: Mapping[str, str],  # the only place NEXAHOME_* variables are read from
        cwd: Path,
        out: TextIO | None = None,
        err: TextIO | None = None,
        disk_free: Callable[[Path], int] = _disk_free,
        now: Callable[[], float] = time.time,
        fetch: Fetcher = _fetch,  # network access, used by `update` only
        download: Downloader = _download,  # the same, streamed to a file (large files)
        ask: Callable[[str], bool | None] = ask_on_terminal,
    ) -> None:
        self.host, self.runner, self.env, self.cwd = host, runner, env, cwd
        self.out = out if out is not None else sys.stdout
        self.err = err if err is not None else sys.stderr
        self.disk_free, self.now, self.fetch, self.download, self.ask = disk_free, now, fetch, download, ask

    @classmethod
    def default(cls) -> "Context":
        return cls(host=current(), runner=SubprocessRunner(), env=dict(os.environ), cwd=Path.cwd())

    def instance(self) -> Path | None:
        """The NexaHome instance (a clone or a folder made by `nexahome init`): see nexahome.instance.home.find.
        --home sets NEXAHOME_HOME for the run. None when there is none."""
        from nexahome.defaults import ENV_HOME
        from nexahome.instance import home  # only commands that need the folder pay for the lookup

        return home.find(self.cwd, self.env.get(ENV_HOME), self.host.home)

    def require_instance(self) -> Path:
        from nexahome.defaults import ENV_HOME

        instance = self.instance()
        if instance is None:
            if self.env.get(ENV_HOME):
                raise NexaHomeError(
                    "NEXAHOME_HOME does not point at a NexaHome instance or clone (a folder with nexahome.toml, or with stacks/ and a Makefile)",
                    'ls "$NEXAHOME_HOME"',
                )
            raise NexaHomeError(
                "no NexaHome instance here: this folder is not inside one (nexahome.toml, or a clone with stacks/ and a Makefile) and ~/nexahome has none",
                "nexahome init",
            )
        return instance

    def display(self, path: Path) -> str:
        """A path for a message or command line: relative to the working directory when inside it."""
        import shlex  # only commands that print paths need it

        try:
            return shlex.quote(str(path.relative_to(self.cwd)))
        except ValueError:
            return shlex.quote(str(path))
