"""The facts about this machine, and what a per-system module provides."""

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class Host:
    system: str  # "macos", "linux" or "windows"
    machine: str  # "arm64", "amd64", or the raw value
    python: tuple[int, int, int]
    home: Path
    debian_like: bool = False  # Linux only: Debian or a derivative


class System(Protocol):
    """One module per operating system satisfies this structurally (see macos.py)."""

    NAME: str
    REFUSAL: tuple[str, str] | None  # (message, fix) when the system is not supported, else None
    MOUNTS_HOME_ONLY: bool  # containers run in a VM that mounts only the home directory (ADR 0004)
    docker_install_fix: Callable[[Host], str]
    compose_install_fix: Callable[[Host], str]
    engine_start_fix: Callable[[Host], str]
    engine_restart_fix: Callable[[Host], str]
