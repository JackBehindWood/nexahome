"""Native Windows is refused; WSL2 counts as Linux (ADR 0019). The fixes only exist to satisfy the interface."""

from nexahome.platform.host import Host

NAME = "windows"
REFUSAL = ("native Windows is not supported; use WSL2, which counts as Linux (best effort)", "wsl --install")
MOUNTS_HOME_ONLY = False


def docker_install_fix(host: Host) -> str:
    return REFUSAL[1]


compose_install_fix = engine_start_fix = engine_restart_fix = docker_install_fix
