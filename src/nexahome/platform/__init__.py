"""Everything that differs between operating systems lives in this package (PK-P3).

No other module reads sys.platform, uname, os-release or builds an OS-specific message. To add a system:
a module here that satisfies host.System, one line in SYSTEMS, and a branch in current(). Systems that are
neither macOS nor Windows are treated as Linux (best effort); WSL2 reports itself as Linux.
"""

import os
import platform as stdlib_platform
import sys
from pathlib import Path

from nexahome.errors import ExitCode, NexaHomeError
from nexahome.platform import linux, macos, windows
from nexahome.platform.host import Host, System

SYSTEMS: dict[str, System] = {"macos": macos, "linux": linux, "windows": windows}
_MACHINES = {"arm64": "arm64", "aarch64": "arm64", "x86_64": "amd64", "amd64": "amd64"}

__all__ = [
    "Host", "SYSTEMS", "colima_mount_applies", "compose_install_fix", "current", "describe",
    "docker_install_fix", "engine_restart_fix", "engine_start_fix", "is_supported_machine", "require_supported",
]


def current() -> Host:
    """Describe the machine this process runs on."""
    if sys.platform == "darwin":
        system = macos.NAME
    elif sys.platform in ("win32", "cygwin"):
        system = windows.NAME
    else:
        system = linux.NAME
    machine = stdlib_platform.machine().lower()
    return Host(
        system=system,
        machine=_MACHINES.get(machine, machine),
        python=(sys.version_info.major, sys.version_info.minor, sys.version_info.micro),
        home=Path(os.path.expanduser("~")),
        debian_like=linux.detect_debian_like() if system == linux.NAME else False,
    )


def describe(host: Host) -> str:
    """For example "macOS arm64"."""
    return f"{'macOS' if host.system == 'macos' else host.system.capitalize()} {host.machine}"


def require_supported(host: Host) -> None:
    """Refuse a system whose module says so; native Windows names WSL2 (PK-P4)."""
    refusal = SYSTEMS[host.system].REFUSAL
    if refusal is not None:
        raise NexaHomeError(refusal[0], refusal[1], ExitCode.NOT_READY)


def is_supported_machine(host: Host) -> bool:
    return host.machine in ("arm64", "amd64")


def colima_mount_applies(host: Host) -> bool:
    return SYSTEMS[host.system].MOUNTS_HOME_ONLY


def docker_install_fix(host: Host) -> str:
    return SYSTEMS[host.system].docker_install_fix(host)


def compose_install_fix(host: Host) -> str:
    return SYSTEMS[host.system].compose_install_fix(host)


def engine_start_fix(host: Host) -> str:
    return SYSTEMS[host.system].engine_start_fix(host)


def engine_restart_fix(host: Host) -> str:
    return SYSTEMS[host.system].engine_restart_fix(host)
