"""Errors that always end in one exact next command."""

from enum import IntEnum


class ExitCode(IntEnum):
    """Exit codes of the nexahome command (ADR 0018, PK-C2)."""

    OK = 0
    FAILED = 1  # a check found a problem (reserved for `check`)
    USAGE = 2  # argparse and unknown commands
    NOT_READY = 3  # the environment is not ready
    INTERRUPTED = 130


class NexaHomeError(Exception):
    """Something the user can fix. `fix` is mandatory: one exact command."""

    def __init__(self, message: str, fix: str, exit_code: ExitCode = ExitCode.NOT_READY) -> None:
        if not fix.strip():
            raise ValueError("a NexaHomeError needs a fix command")
        super().__init__(message)
        self.message = message
        self.fix = fix
        self.exit_code = exit_code
