"""Linux (WSL2 reports itself as Linux; any other POSIX system is treated as Linux, best effort)."""

from pathlib import Path

from nexahome.platform.host import Host

NAME = "linux"
REFUSAL = None
MOUNTS_HOME_ONLY = False
INSTALL_PAGE = "https://docs.docker.com/engine/install/"


def parse_os_release(text: str) -> bool:
    """True when the os-release text describes Debian or a derivative."""
    ids: set[str] = set()
    for line in text.splitlines():
        key, _, value = line.partition("=")
        if key in ("ID", "ID_LIKE"):
            ids.update(value.strip().strip('"').lower().split())
    return bool(ids & {"debian", "ubuntu"})


def detect_debian_like() -> bool:
    try:
        return parse_os_release(Path("/etc/os-release").read_text())
    except OSError:
        return False


def docker_install_fix(host: Host) -> str:
    if host.debian_like:
        return "sudo apt-get install docker.io docker-compose-v2"
    return INSTALL_PAGE  # no single command fits every distribution (the one documented exception)


def compose_install_fix(host: Host) -> str:
    if host.debian_like:
        return "sudo apt-get install docker-compose-v2"
    return INSTALL_PAGE


def engine_start_fix(host: Host) -> str:
    return "sudo systemctl start docker"


def engine_restart_fix(host: Host) -> str:
    return "sudo systemctl restart docker"
