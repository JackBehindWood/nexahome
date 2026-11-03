"""The one place that starts other programs."""

from collections.abc import Sequence
from typing import NamedTuple, Protocol


class RunResult(NamedTuple):
    """What a command did; a missing program or a timeout is a result, not an exception."""

    returncode: int
    stdout: str = ""
    stderr: str = ""
    missing: bool = False  # the program was not found or not executable
    timed_out: bool = False

    @property
    def ok(self) -> bool:
        return self.returncode == 0 and not self.missing and not self.timed_out


class Runner(Protocol):
    """Runs a command line without a shell; tests replace it."""

    def run(self, argv: Sequence[str], *, timeout: float) -> RunResult: ...


class SubprocessRunner:
    """Runs argv lists without a shell. A missing program or a timeout is a result, not an exception."""

    def run(self, argv: Sequence[str], *, timeout: float) -> RunResult:
        import subprocess

        try:
            done = subprocess.run(
                list(argv),
                capture_output=True,
                text=True,
                errors="replace",
                timeout=timeout,
                stdin=subprocess.DEVNULL,
                check=False,
            )
        except (FileNotFoundError, PermissionError) as error:
            return RunResult(127, stderr=str(error), missing=True)
        except subprocess.TimeoutExpired:
            return RunResult(124, timed_out=True)
        return RunResult(done.returncode, done.stdout, done.stderr)
