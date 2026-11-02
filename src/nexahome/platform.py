"""Everything that differs between operating systems lives in this module (PK-P3).

No other module reads sys.platform, uname, os-release or builds an OS-specific message. Systems that are
neither macOS nor Windows are treated as Linux (best effort); WSL2 reports itself as Linux.
"""

import os
import platform as stdlib_platform
import sys
from dataclasses import dataclass
from pathlib import Path

from nexahome.errors import ExitCode, NexaHomeError

_MACHINES = {"arm64": "arm64", "aarch64": "arm64", "x86_64": "amd64", "amd64": "amd64"}
_INSTALL_PAGE = "https://docs.docker.com/engine/install/"


@dataclass(frozen=True)
class Host:
    """The facts about this machine that the rest of the package may use."""

    system: str  # "macos", "linux" or "windows"
    machine: str  # "arm64", "amd64", or the raw value
    python: tuple[int, int, int]
    home: Path
    debian_like: bool = False


def parse_os_release(text: str) -> bool:
    """True when the os-release text describes Debian or a derivative."""
    ids: set[str] = set()
    for line in text.splitlines():
        key, _, value = line.partition("=")
        if key in ("ID", "ID_LIKE"):
            ids.update(value.strip().strip('"').lower().split())
    return bool(ids & {"debian", "ubuntu"})


def current() -> Host:
    """Describe the machine this process runs on."""
    if sys.platform == "darwin":
        system = "macos"
    elif sys.platform in ("win32", "cygwin"):
        system = "windows"
    else:
        system = "linux"
    machine = stdlib_platform.machine().lower()
    debian_like = False
    if system == "linux":
        try:
            debian_like = parse_os_release(Path("/etc/os-release").read_text())
        except OSError:
            pass
    return Host(
        system=system,
        machine=_MACHINES.get(machine, machine),
        python=(sys.version_info.major, sys.version_info.minor, sys.version_info.micro),
        home=Path(os.path.expanduser("~")),
        debian_like=debian_like,
    )


def describe(host: Host) -> str:
    """For example "macOS arm64"."""
    return f"{'macOS' if host.system == 'macos' else host.system.capitalize()} {host.machine}"


def require_supported(host: Host) -> None:
    """Refuse native Windows with a message that names WSL2 (PK-P4)."""
    if host.system == "windows":
        raise NexaHomeError(
            "native Windows is not supported; use WSL2, which counts as Linux (best effort)",
            "wsl --install",
        )


def is_supported_machine(host: Host) -> bool:
    return host.machine in ("arm64", "amd64")


def colima_mount_applies(host: Host) -> bool:
    """macOS runs containers in a VM that mounts only the home directory (ADR 0004)."""
    return host.system == "macos"


def docker_install_fix(host: Host) -> str:
    if host.system == "macos":
        return "brew install colima docker docker-compose"
    if host.debian_like:
        return "sudo apt-get install docker.io docker-compose-v2"
    return _INSTALL_PAGE  # no single command fits every distribution (the one documented exception)


def compose_install_fix(host: Host) -> str:
    if host.system == "macos":
        return (
            "brew install docker-compose && mkdir -p ~/.docker/cli-plugins && "
            'ln -sfn "$(brew --prefix)/opt/docker-compose/bin/docker-compose" ~/.docker/cli-plugins/docker-compose'
        )
    if host.debian_like:
        return "sudo apt-get install docker-compose-v2"
    return _INSTALL_PAGE


def engine_start_fix(host: Host) -> str:
    if host.system == "macos":
        return "colima start --cpu 2 --memory 2 --disk 20"
    return "sudo systemctl start docker"


def engine_restart_fix(host: Host) -> str:
    if host.system == "macos":
        return "colima restart"
    return "sudo systemctl restart docker"
